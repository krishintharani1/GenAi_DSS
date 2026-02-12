import json
from typing import List, Tuple, Optional
from .base_agent import BaseAgent
from ..config import StoryConfig
from ..schemas import StoryState
from ..prompts.director_prompts import DIRECTOR_SELECT_SPEAKER_PROMPT, DIRECTOR_CONCLUSION_PROMPT

class DirectorAgent(BaseAgent):
    def __init__(self, config: StoryConfig):
        super().__init__("Director", config)
    
    async def select_next_speaker(self, story_state: StoryState, available_characters: List[str]) -> str:
        """Decide who speaks next."""
        # Format context
        if story_state.dialogue_history:
            recent_dialogue = "\n".join(
                f"{turn.speaker}: {turn.dialogue}" 
                for turn in story_state.dialogue_history[-5:]
            )
        else:
            recent_dialogue = "No dialogue yet. The story is just starting. Select the character most likely to speak first based on the Context."
        
        prompt = DIRECTOR_SELECT_SPEAKER_PROMPT.format(
            story_context=story_state.seed_story.get('context', ''),
            recent_dialogue=recent_dialogue,
            available_characters=", ".join(available_characters),
            max_consecutive=self.config.max_consecutive_same_character
        )
        
        # print(f"DEBUG: Director Prompt:\n{prompt}\n")
        response = await self.generate_response(prompt)
        print(f"DEBUG: Director Raw Response:\n{response}\n")
        
        try:
            # Clean json block if needed
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0]
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0]
            
            data = json.loads(cleaned_response)
            next_speaker = data.get("next_speaker")
            
            if next_speaker in available_characters:
                return next_speaker
            return available_characters[0]
            
        except Exception as e:
            print(f"Error parsing director selection: {e}")
            print(f"Raw response: {response}")
            return available_characters[0]

    async def check_conclusion(self, story_state: StoryState) -> Tuple[bool, Optional[str]]:
        """Check if the story should end."""
        prompt = DIRECTOR_CONCLUSION_PROMPT.format(
            story_summary=f"Context: {story_state.seed_story.get('context', '')}\nLast Turns:\n" + "\n".join([f"{t.speaker}: {t.dialogue}" for t in story_state.dialogue_history[-5:]]),
            current_turn=story_state.current_turn,
            max_turns=self.config.max_turns,
            min_turns=self.config.min_turns
        )
        
        response = await self.generate_response(prompt)
        
        try:
            # Clean json block if needed
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            data = json.loads(response.strip())
            return data.get("should_end", False), data.get("conclusion_narration")
        except Exception as e:
            print(f"Error parsing director conclusion: {e}")
            return False, None
