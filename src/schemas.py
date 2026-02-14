from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DialogueTurn(BaseModel):
    turn_number: int
    speaker: str
    dialogue: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Action(BaseModel):
    """Represents a non-verbal action performed by a character."""
    turn_number: int
    actor: str
    action_type: str  # e.g., "leave_room", "search_object", "trade_item", "unlock_door", "betray_ally"
    target: Optional[str] = None  # Target of the action (object, location, person)
    description: str  # Narrative description of the action
    timestamp: datetime = Field(default_factory=datetime.now)
    effects: Dict[str, Any] = Field(default_factory=dict)  # State changes caused by action

class CharacterMemory(BaseModel):
    """Memory buffer for a character."""
    character_name: str
    observations: List[str] = Field(default_factory=list)  # What they've observed
    inventory: List[str] = Field(default_factory=list)  # Items they possess
    goals: List[str] = Field(default_factory=list)  # Current goals
    perceptions: Dict[str, str] = Field(default_factory=dict)  # Perceptions of other characters
    important_facts: List[str] = Field(default_factory=list)  # Key facts to remember

class CharacterProfile(BaseModel):
    name: str
    description: str
    secret: str = ""  # Hidden motivation only this character knows
    memory: CharacterMemory = None
    initial_inventory: List[str] = Field(default_factory=list)
    initial_goals: List[str] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.memory is None:
            self.memory = CharacterMemory(
                character_name=self.name,
                inventory=self.initial_inventory.copy(),
                goals=self.initial_goals.copy(),
                # Seed the secret as an important fact only this character knows
                important_facts=[f"SECRET: {self.secret}"] if self.secret else []
            )

class StoryState(BaseModel):
    seed_story: Dict[str, Any]
    current_turn: int = 0
    story_narration: List[str] = []
    dialogue_history: List[DialogueTurn] = Field(default_factory=list)
    action_history: List[Action] = Field(default_factory=list)  # Track all actions
    events: List[Dict[str, Any]] = Field(default_factory=list)
    character_profiles: Dict[str, CharacterProfile] = Field(default_factory=dict)
    director_notes: List[str] = Field(default_factory=list)
    next_speaker: Optional[str] = None
    is_concluded: bool = False
    conclusion_reason: Optional[str] = None
    world_state: Dict[str, Any] = Field(default_factory=dict)  # Global world state (locations, objects, etc.)