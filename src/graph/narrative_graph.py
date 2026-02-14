from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
from ..config import StoryConfig
from ..schemas import StoryState, DialogueTurn, Action
from ..agents.character_agent import CharacterAgent
from ..agents.director_agent import DirectorAgent
from ..story_state import StoryStateManager

class NarrativeGraph:
    def __init__(self, config: StoryConfig, characters: List[CharacterAgent], 
                 director: DirectorAgent):
        self.config = config
        self.characters = {c.name: c for c in characters}
        self.director = director
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(StoryState)
        
        # Add nodes
        workflow.add_node("director_select", self._director_select_node)
        workflow.add_node("character_respond", self._character_respond_node)
        workflow.add_node("check_conclusion", self._check_conclusion_node)
        workflow.add_node("conclude", self._conclude_node)
        
        # Add edges
        workflow.set_entry_point("director_select")
        
        workflow.add_edge("director_select", "character_respond")
        workflow.add_edge("character_respond", "check_conclusion")
        
        # Conditional edge for conclusion
        workflow.add_conditional_edges(
            "check_conclusion",
            self._route_conclusion,
            {
                "conclude": "conclude",
                "continue": "director_select"
            }
        )
        
        workflow.add_edge("conclude", END)
        
        return workflow.compile()
    
    async def _director_select_node(self, state: StoryState) -> Dict:
        """Director selects the next speaker."""
        available = list(self.characters.keys())
        next_speaker, narration = await self.director.select_next_speaker(state, available)

        print("=" * 60)
        print(f"DIRECTOR NARRATION: {narration}")
        print(f"NEXT SPEAKER: {next_speaker}")
        print(f"Turn: {state.current_turn + 1}/{self.config.max_turns}")
        print(f"Actions so far: {len(state.action_history)}")
        print("=" * 60 + "\n")

        # Create event log for narration if it exists
        events_update = []
        if narration:
            events_update.append({
                "type": "narration",
                "content": narration,
                "turn": state.current_turn
            })
            
        return {
            "next_speaker": next_speaker,
            "director_notes": state.director_notes + [f"Selected: {next_speaker}"],
            "story_narration": state.story_narration + [narration] if narration else state.story_narration,
            "events": state.events + events_update
        }
    
    async def _character_respond_node(self, state: StoryState) -> Dict:
        """Selected character generates dialogue or performs action."""
        next_speaker = state.next_speaker
        
        # Fallback if somehow None (shouldn't happen with correct flow)
        if not next_speaker or next_speaker not in self.characters:
            next_speaker = list(self.characters.keys())[0] 
            
        character = self.characters[next_speaker]
        
        # Build context using updated method
        # Taking last 10 turns
        recent_turns = state.dialogue_history[-10:]
        history_text = "\n".join([
            f"{turn.speaker}: {turn.dialogue}"
            for turn in recent_turns
        ])
        
        # Include recent actions
        recent_actions = state.action_history[-5:]
        actions_text = "\n".join([
            f"[ACTION] {action.actor}: {action.description}"
            for action in recent_actions
        ])
        
        char_memory = state.character_profiles[next_speaker].memory
        
        context = f"""
Initial Event: {state.seed_story.get('description', 'Unknown event')}

World State:
Location: {state.world_state.get('location', 'Unknown')}
Characters Present: {', '.join(state.world_state.get('characters_present', []))}

Your Memory:
Inventory: {', '.join(char_memory.inventory) if char_memory.inventory else 'None'}
Goals: {', '.join(char_memory.goals) if char_memory.goals else 'None'}
Recent Observations: {'; '.join(char_memory.observations[-3:]) if char_memory.observations else 'None'}

Director Narration: {state.story_narration[-1] if state.story_narration else 'None'}

Recent Actions:
{actions_text if actions_text else 'No actions yet'}

Recent Dialogue:
{history_text if history_text else 'No dialogue yet'}
"""
        
        response, action_dict = await character.respond(state, context)

        new_turn = state.current_turn + 1
        events_update = []
        action_history_update = []
        
        if action_dict:
            # This is an action
            print("=" * 60)
            print(f"[ACTION] {next_speaker}: {action_dict['action_type'].upper()}")
            print(f"Description: {response}")
            if action_dict.get('action_target'):
                print(f"Target: {action_dict['action_target']}")
            print("=" * 60 + "\n")
            
            # Create action object
            action_obj = Action(
                turn_number=new_turn,
                actor=next_speaker,
                action_type=action_dict['action_type'],
                target=action_dict.get('action_target'),
                description=response,
                effects=action_dict.get('effects', {})
            )
            action_history_update.append(action_obj)
            
            # Create event log for action
            events_update.append({
                "type": "action",
                "actor": next_speaker,
                "action_type": action_dict['action_type'],
                "content": response,
                "turn": new_turn
            })
            
            # Update world state with effects
            world_state_update = {**state.world_state, **action_dict.get('effects', {})}
            
            # Update character memory
            char_memory.observations.append(f"I performed action: {response}")
            
            return {
                "action_history": state.action_history + action_history_update,
                "current_turn": new_turn,
                "events": state.events + events_update,
                "world_state": world_state_update
            }
        else:
            # Regular dialogue
            print("=" * 60)
            print(f"{next_speaker}: {response}")
            print("=" * 60 + "\n")
            
            # Update state with new turn
            new_turn_obj = DialogueTurn(
                turn_number=new_turn,
                speaker=next_speaker,
                dialogue=response
            )
            
            # Create event log for dialogue
            events_update.append({
                "type": "dialogue",
                "speaker": next_speaker,
                "content": response,
                "turn": new_turn
            })
            
            # Update character memory
            char_memory.observations.append(f"I said: {response}")
            
            return {
                "dialogue_history": state.dialogue_history + [new_turn_obj],
                "current_turn": new_turn,
                "events": state.events + events_update
            }
    
    async def _check_conclusion_node(self, state: StoryState) -> Dict:
        """Check if story should end."""
        should_end, reason = await self.director.check_conclusion(state)
        
        # Also check if we have minimum actions
        action_count = len(state.action_history)
        
        if should_end:
            # Warn if we don't have enough actions
            if action_count < self.config.min_actions:
                print(f"\n!!! WARNING: Story ending with only {action_count} actions (minimum {self.config.min_actions} required) !!!\n")
            
            # Create event log for conclusion
            events_update = []
            if reason:
                 events_update.append({
                     "type": "narration",
                     "content": reason,
                     "turn": state.current_turn,
                     "metadata": {"conclusion": True}
                 })
                 
            return {
                "is_concluded": True, 
                "conclusion_reason": str(reason),
                "events": state.events + events_update
            }
        return {"is_concluded": False}
    
    async def _conclude_node(self, state: StoryState) -> Dict:
        """Finalize story."""
        return {"is_concluded": True}

    def _route_conclusion(self, state: StoryState) -> str:
        if state.is_concluded:
            return "conclude"
        return "continue"
    
    async def run(self, seed_story: Dict, character_profiles: Dict[str, Any] = None) -> StoryState:
        """Execute the narrative game loop"""
        initial_state = StoryState(
            seed_story=seed_story,
            character_profiles=character_profiles or {},
            dialogue_history=[],
            director_notes=[],
            world_state={
                "location": "Shahrah-e-Faisal near Karachi Airport",
                "time": "late afternoon",
                "traffic_cleared": False,
                "accident_resolved": False,
                "characters_present": list(character_profiles.keys()) if character_profiles else []
            }
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
