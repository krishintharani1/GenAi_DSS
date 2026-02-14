from typing import List, Dict, Tuple, Optional
from datetime import datetime
from .schemas import StoryState, CharacterProfile, DialogueTurn, Action, CharacterMemory
from .config import StoryConfig

class StoryStateManager:
    def __init__(self, seed_story: Dict, characters: List[Dict], config: StoryConfig):
        self.config = config
        self.state = StoryState(
            seed_story=seed_story,
            character_profiles={
                char["name"]: CharacterProfile(
                    name=char["name"],
                    description=char["description"],
                    initial_inventory=char.get("initial_inventory", []),
                    initial_goals=char.get("initial_goals", [])
                ) for char in characters
            },
            world_state={
                "location": "Shahrah-e-Faisal near Karachi Airport",
                "time": "late afternoon",
                "traffic_cleared": False,
                "accident_resolved": False,
                "characters_present": [char["name"] for char in characters]
            }
        )
    
    def add_turn(self, speaker: str, dialogue: str, metadata: Dict = None) -> None:
        """Add a dialogue turn and increment turn count."""
        turn = DialogueTurn(
            turn_number=self.state.current_turn + 1,
            speaker=speaker,
            dialogue=dialogue,
            metadata=metadata or {}
        )
        self.state.dialogue_history.append(turn)
        self.state.current_turn += 1
        
        # Update character memory with their own dialogue
        if speaker in self.state.character_profiles:
            char_memory = self.state.character_profiles[speaker].memory
            char_memory.observations.append(f"I said: {dialogue}")
    
    def add_action(self, actor: str, action_type: str, target: Optional[str], 
                   description: str, effects: Dict = None) -> None:
        """Add an action and update story state."""
        action = Action(
            turn_number=self.state.current_turn,
            actor=actor,
            action_type=action_type,
            target=target,
            description=description,
            effects=effects or {}
        )
        self.state.action_history.append(action)
        
        # Apply effects to world state
        if effects:
            self.state.world_state.update(effects)
        
        # Update actor's memory
        if actor in self.state.character_profiles:
            char_memory = self.state.character_profiles[actor].memory
            char_memory.observations.append(f"I performed action: {description}")
        
        # Update other characters' memory (they observe the action)
        for char_name in self.state.character_profiles:
            if char_name != actor and char_name in self.state.world_state.get("characters_present", []):
                char_memory = self.state.character_profiles[char_name].memory
                char_memory.observations.append(f"{actor} performed action: {description}")
    
    def update_character_memory(self, character_name: str, observation: str = None,
                               fact: str = None, perception: Dict[str, str] = None) -> None:
        """Update a character's memory."""
        if character_name not in self.state.character_profiles:
            return
        
        memory = self.state.character_profiles[character_name].memory
        
        if observation:
            memory.observations.append(observation)
        if fact:
            memory.important_facts.append(fact)
        if perception:
            memory.perceptions.update(perception)
    
    def get_context_for_character(self, character_name: str) -> str:
        """Return relevant context for a character, including their memory."""
        if character_name not in self.state.character_profiles:
            return ""
        
        char_profile = self.state.character_profiles[character_name]
        char_memory = char_profile.memory
        
        # Get recent dialogue (last 10 turns)
        recent_turns = self.state.dialogue_history[-10:]
        history_text = "\n".join([
            f"{turn.speaker}: {turn.dialogue}"
            for turn in recent_turns
        ])
        
        # Get recent actions (last 5)
        recent_actions = self.state.action_history[-5:]
        actions_text = "\n".join([
            f"[ACTION] {action.actor}: {action.description}"
            for action in recent_actions
        ])
        
        # Build memory summary
        memory_text = f"""
Your Inventory: {', '.join(char_memory.inventory) if char_memory.inventory else 'None'}
Your Goals: {', '.join(char_memory.goals) if char_memory.goals else 'None'}
Key Facts You Remember: {'; '.join(char_memory.important_facts[-5:]) if char_memory.important_facts else 'None'}
Your Recent Observations: {'; '.join(char_memory.observations[-5:]) if char_memory.observations else 'None'}
"""
        
        return f"""
Initial Event: {self.state.seed_story.get('description', 'Unknown event')}

World State:
Location: {self.state.world_state.get('location', 'Unknown')}
Characters Present: {', '.join(self.state.world_state.get('characters_present', []))}

Your Memory:
{memory_text}

Recent Actions:
{actions_text if actions_text else 'No actions yet'}

Recent Dialogue:
{history_text if history_text else 'No dialogue yet'}
"""
        
    def get_context_for_director(self) -> str:
        """Return full story context for director decisions."""
        history_text = "\n".join([
            f"[{turn.turn_number}] {turn.speaker}: {turn.dialogue}"
            for turn in self.state.dialogue_history
        ])
        
        actions_text = "\n".join([
            f"[{action.turn_number}] ACTION by {action.actor}: {action.description}"
            for action in self.state.action_history
        ])
        
        return f"""
Story Title: {self.state.seed_story.get('title', 'Untitled')}
Description: {self.state.seed_story.get('description', '')}

World State: {self.state.world_state}

Actions Performed ({len(self.state.action_history)} total):
{actions_text if actions_text else 'No actions yet'}

Dialogue History:
{history_text}

Director Notes:
{chr(10).join(self.state.director_notes)}
"""

    def should_end_story(self) -> Tuple[bool, str]:
        """Check if story should conclude based on turn limits."""
        if self.state.current_turn >= self.config.max_turns:
            return True, "Max turns reached"
        if self.state.is_concluded:
            return True, self.state.conclusion_reason or "Director concluded story"
        return False, ""
    
    def get_action_count(self) -> int:
        """Get total number of actions performed."""
        return len(self.state.action_history)

