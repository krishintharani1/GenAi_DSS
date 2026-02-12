from ..schemas import CharacterState

def get_character_prompt(character_name: str, character_state: CharacterState, context: str, config) -> str:
    goals_str = "\n".join(f"- {goal}" for goal in character_state.goals)
    memory_str = "\n".join(f"- {mem}" for mem in character_state.memory) if character_state.memory else "None"
    
    return f"""You are {character_name}, a character in a story set in Karachi, Pakistan.
Your Personality: {character_state.name}
Your Current Goals:
{goals_str}
Current Situation:
{context}
Your Current Emotional State: {character_state.emotional_state}
Things You Remember:
{memory_str}

Respond as {character_name} would in this situation. Stay in character and speak naturally in the context of Karachi culture. Keep your response under {config.max_dialogue_length} tokens.
Response (dialogue only, no actions):
"""
