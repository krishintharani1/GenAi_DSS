import json
from typing import List, Tuple, Optional
from .base_agent import BaseAgent
from ..config import StoryConfig
from ..schemas import StoryState
from ..prompts.director_prompts import (
    DIRECTOR_SELECT_SPEAKER_PROMPT, 
    DIRECTOR_CONCLUSION_PROMPT,
    DIRECTOR_FORCE_CONCLUDE_PROMPT
)

class DirectorAgent(BaseAgent):
    def __init__(self, config: StoryConfig):
        super().__init__("Director", config)
    
    async def select_next_speaker(self, story_state: StoryState, 
                                   available_characters: List[str],
                                   previous_narrations: List[str] = None) -> str:
        """Decide who speaks next."""
        # Format context
        if story_state.dialogue_history:
            recent_dialogue = "\n".join(
                f"{turn.speaker}: {turn.dialogue}" 
                for turn in story_state.dialogue_history[-5:]
            )
        else:
            recent_dialogue = "No dialogue yet. The situation just occurred. Select the person most likely to react first."
        
        # Format recent actions
        if story_state.action_history:
            recent_actions = "\n".join(
                f"[ACTION] {action.actor}: {action.description}"
                for action in story_state.action_history[-3:]
            )
        else:
            recent_actions = "No actions performed yet."
        
        # Build character secrets summary
        character_secrets = []
        for char_name in available_characters:
            profile = story_state.character_profiles.get(char_name)
            if profile and profile.secret:
                character_secrets.append(f"- {char_name}: {profile.secret}")
        character_secrets_text = "\n".join(character_secrets) if character_secrets else "No secrets defined."
        
        # Build previous narrations for anti-repetition
        if previous_narrations:
            prev_narrations_text = "\n".join([f"- {n}" for n in previous_narrations])
        else:
            prev_narrations_text = "None yet."
        
        prompt = DIRECTOR_SELECT_SPEAKER_PROMPT.format(
            description=story_state.seed_story.get('description', ''),
            recent_dialogue=recent_dialogue,
            recent_actions=recent_actions,
            available_characters=", ".join(available_characters),
            max_consecutive=self.config.max_consecutive_same_character,
            character_secrets=character_secrets_text,
            previous_narrations=prev_narrations_text
        )
        
        response = await self.generate_response(prompt)
        
        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            next_speaker = data.get("next_speaker")
            narration = data.get("narration")
            
            if next_speaker in available_characters:
                return next_speaker, narration
            return available_characters[0], narration
            
        except Exception as e:
            print(f"Error parsing director selection: {e}")
            print(f"Raw response: {response}")
            return available_characters[0], ""

    async def check_conclusion(self, story_state: StoryState) -> Tuple[bool, Optional[str]]:
        """Check if the story should end."""
        action_count = len(story_state.action_history)
        
        prompt = DIRECTOR_CONCLUSION_PROMPT.format(
            story_summary=f"Context: {story_state.seed_story.get('description', '')}\nLast Turns:\n" + "\n".join([f"{t.speaker}: {t.dialogue}" for t in story_state.dialogue_history[-5:]]),
            action_count=action_count,
            current_turn=story_state.current_turn,
            max_turns=self.config.max_turns,
            min_turns=self.config.min_turns,
            min_actions=self.config.min_actions
        )
        
        response = await self.generate_response(prompt)
        
        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            should_end = data.get("should_end", False)
            
            if should_end and action_count < self.config.min_actions and story_state.current_turn < self.config.max_turns:
                print(f"  [Director wanted to end, but only {action_count}/{self.config.min_actions} actions performed. Continuing...]")
                return False, None
            
            if should_end and story_state.current_turn < self.config.min_turns:
                print(f"  [Director wanted to end at turn {story_state.current_turn}, but min_turns is {self.config.min_turns}. Continuing...]")
                return False, None
                
            return should_end, data.get("conclusion_narration")
        except Exception as e:
            print(f"Error parsing director conclusion: {e}")
            return False, None

    async def force_conclude(self, story_state: StoryState) -> Tuple[bool, Optional[str]]:
        """Force the Director to write a proper narrative conclusion when max turns are hit."""
        action_count = len(story_state.action_history)
        
        key_events = []
        for event in story_state.events[-10:]:
            if event.get("type") == "action":
                key_events.append(f"[ACTION] {event.get('actor')}: {event.get('content')}")
            elif event.get("type") == "dialogue":
                key_events.append(f"{event.get('speaker')}: {event.get('content')}")
        
        prompt = DIRECTOR_FORCE_CONCLUDE_PROMPT.format(
            story_context=story_state.seed_story.get('description', ''),
            key_events="\n".join(key_events) if key_events else "No major events.",
            last_dialogue="\n".join([f"{t.speaker}: {t.dialogue}" for t in story_state.dialogue_history[-3:]]),
            action_count=action_count,
            total_turns=story_state.current_turn
        )
        
        response = await self.generate_response(prompt)
        
        try:
            cleaned_response = self._clean_json_response(response)
            data = json.loads(cleaned_response)
            return True, data.get("conclusion_narration", "The scene fades as the dust settles on Shahrah-e-Faisal.")
        except Exception as e:
            print(f"Error parsing forced conclusion: {e}")
            return True, "The scene fades as the dust settles on Shahrah-e-Faisal."