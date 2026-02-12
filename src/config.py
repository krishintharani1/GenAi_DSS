from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class StoryConfig:
    """Configuration for the story simulation."""
    # Model settings
    model_name: str = "gemma-3-27b-it"
    temperature: float = 0.7
    
    # Constraints (Phase 1)
    max_turns: int = 25
    min_turns: int = 15
    max_tokens_per_prompt: int = 2000
    max_context_length: int = 4000
    
    # Director settings
    turns_between_director_intervention: int = 5
    max_consecutive_same_character: int = 2
    
    # Character settings
    num_characters: int = 4
    max_dialogue_length: int = 200  # tokens
    
    # Story settings
    allow_actions: bool = False  # Phase 1: dialogue only
    enable_random_events: bool = False  # Phase 2 feature
