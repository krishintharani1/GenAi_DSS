from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
from ..config import StoryConfig
from ..schemas import StoryState, DialogueTurn
from ..agents.character_agent import CharacterAgent
from ..agents.director_agent import DirectorAgent
from ..story_state import StoryStateManager, get_character_context

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
        next_speaker = await self.director.select_next_speaker(state, available)

        # Update the structured state instead of append-only notes
        return {
            "next_speaker": next_speaker,
            "director_notes": state.director_notes + [f"Selected: {next_speaker}"]
        }
    
    async def _character_respond_node(self, state: StoryState) -> Dict:
        """Selected character generates dialogue."""
        next_speaker = state.next_speaker
        
        # Fallback if somehow None (shouldn't happen with correct flow)
        if not next_speaker or next_speaker not in self.characters:
            next_speaker = list(self.characters.keys())[0] 
            
        character = self.characters[next_speaker]
        
        # Get context
        context = get_character_context(state, next_speaker)
        
        response = await character.respond(state, context)
        
        # Update state with new turn
        new_turn = DialogueTurn(
            turn_number=state.current_turn + 1,
            speaker=next_speaker,
            dialogue=response
        )
        
        return {
            "dialogue_history": state.dialogue_history + [new_turn],
            "current_turn": state.current_turn + 1
        }
    
    async def _check_conclusion_node(self, state: StoryState) -> Dict:
        """Check if story should end."""
        should_end, reason = await self.director.check_conclusion(state)
        
        if should_end:
            return {
                "is_concluded": True, 
                "conclusion_reason": str(reason) # reason can be tuple if narration included
            }
        return {"is_concluded": False}
    
    async def _conclude_node(self, state: StoryState) -> Dict:
        """Finalize story."""
        return {"is_concluded": True}

    def _route_conclusion(self, state: StoryState) -> str:
        if state.is_concluded:
            return "conclude"
        return "continue"
    
    async def run(self, seed_story: Dict, character_states: Dict[str, Any] = None) -> StoryState:
        """Execute the narrative game loop"""
        initial_state = StoryState(
            seed_story=seed_story,
            character_states=character_states or {},
            dialogue_history=[],
            director_notes=[]
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
