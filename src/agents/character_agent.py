import json
from typing import List, Dict, Tuple, Optional
from .base_agent import BaseAgent
from ..config import StoryConfig
from ..schemas import StoryState, CharacterProfile
from ..prompts.character_prompts import get_character_prompt

class CharacterAgent(BaseAgent):
    def __init__(self, name: str, config: StoryConfig):
        super().__init__(name, config)

    async def respond(self, story_state: StoryState, context: str) -> Tuple[str, Optional[Dict]]:
        """Generate a response based on the current story state and context.
        
        Returns:
            Tuple of (response_text, action_dict or None)
            action_dict has keys: action_type, action_target, description, effects
        """
        
        # Get character profile
        character_profile = story_state.character_profiles.get(self.name)
        
        # Build prompt
        prompt = get_character_prompt(
            character_name=self.name,
            character_profile=character_profile,
            context=context,
            config=self.config
        )
        
        try:
            content = await self.generate_response(prompt)
            content = content.strip()
            
            # Try to parse JSON response
            try:
                cleaned_response = self._clean_json_response(content)
                response_data = json.loads(cleaned_response)
                
                action_type = response_data.get("action_type", "TALK")
                reasoning = response_data.get("reasoning", "")
                response_text = response_data.get("response", "")
                
                # Log reasoning
                if reasoning:
                    print(f"  [{self.name} thinks: {reasoning}]")
                
                if action_type != "TALK":
                    # This is an action
                    action_dict = {
                        "action_type": action_type.lower(),
                        "action_target": response_data.get("action_target"),
                        "description": response_text,
                        "effects": self._determine_action_effects(
                            action_type, 
                            response_data.get("action_target"),
                            story_state
                        )
                    }
                    return response_text, action_dict
                else:
                    # Regular dialogue
                    return response_text, None
                    
            except json.JSONDecodeError:
                # Fallback: treat as regular dialogue
                print(f"  [Warning: Could not parse JSON from {self.name}, treating as dialogue]")
                return content, None
                
        except Exception as e:
            print(f"Error in character response: {e}")
            return "...", None
    
    def _determine_action_effects(self, action_type: str, target: Optional[str], 
                                  story_state: StoryState) -> Dict:
        """Determine the effects of an action on the story state."""
        effects = {}
        action_type = action_type.upper()
        
        if action_type == "LEAVE":
            # Character leaves the scene
            characters_present = story_state.world_state.get("characters_present", [])
            if self.name in characters_present:
                updated_present = [c for c in characters_present if c != self.name]
                effects["characters_present"] = updated_present
                
        elif action_type == "CALL":
            # Character makes a phone call
            effects[f"{self.name}_on_call"] = True
            
        elif action_type == "GIVE" and target:
            # Transfer item from inventory
            char_memory = story_state.character_profiles[self.name].memory
            if char_memory.inventory:
                # Assume giving first relevant item
                effects[f"item_given_to_{target}"] = True
                
        elif action_type == "THREATEN":
            effects["tension_level"] = "high"
            
        return effects
