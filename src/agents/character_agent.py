from typing import List, Dict
from .base_agent import BaseAgent
from ..config import StoryConfig
from ..schemas import StoryState, CharacterState
from ..prompts.character_prompts import get_character_prompt

class CharacterAgent(BaseAgent):
    def __init__(self, name: str, config: StoryConfig):
        super().__init__(name, config)
        self._current_context = ""
        self._current_state: CharacterState = None

    async def respond(self, story_state: StoryState, context: str) -> str:
        """Generate a response based on the current story state and context."""
        # Update internal state tracker
        self._current_state = story_state.character_states.get(self.name)
        self._current_context = context

        # Build prompt
        prompt = get_character_prompt(
            character_name=self.name,
            character_state=self._current_state,
            context=context,
            config=self.config
        )
        
        # print(f"DEBUG: {self.name} Prompt:\n{prompt}\n")
        
        messages = [
            ("human", prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            print(f"DEBUG: {self.name} Response: {content[:50]}...")
            return content
        except Exception as e:
            print(f"Error in character response: {e}")
            return "..."
