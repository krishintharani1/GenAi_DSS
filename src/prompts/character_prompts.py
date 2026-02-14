from ..schemas import CharacterProfile

def get_character_prompt(character_name: str, character_profile: CharacterProfile, context: str, config) -> str:
    
    return f"""You are {character_name}, a character in a story set in Karachi, Pakistan.
Your Personality: {character_profile.description}

Current Situation:
{context}

IMPORTANT INSTRUCTIONS:
You can either TALK or perform an ACTION. You must decide which is more appropriate.

Available Actions:
- LEAVE: Leave the current location
- SEARCH: Search for an object or information
- GIVE: Give an item to another character
- TAKE: Take an item from someone or somewhere
- CALL: Make a phone call
- SHOW: Show something to someone
- THREATEN: Make a threatening gesture
- GESTURE: Make a significant non-verbal gesture
- MOVE: Move to a different position or location

REASONING PROCESS:
1. First, think about your current goals and what you're trying to achieve
2. Consider if talking alone will help you progress toward your goals
3. If dialogue is stuck or insufficient, consider performing an action

RESPONSE FORMAT - You must respond in JSON format:
{{
    "reasoning": "Brief explanation of what you're thinking and why you chose this response",
    "action_type": "TALK" or one of the action types above,
    "action_target": "target of action (only if action_type is not TALK)",
    "response": "your dialogue (if TALK) or description of action being performed"
}}

Keep your response under {config.max_dialogue_length} tokens.
Respond as {character_name} would, staying true to your personality and goals.
"""

def get_character_reasoning_prompt(character_name: str, character_profile: CharacterProfile, 
                                  context: str, recent_dialogue: str) -> str:
    """Get a prompt specifically for the reasoning phase."""
    return f"""You are {character_name}.
Your Personality: {character_profile.description}

Current Context:
{context}

Recent Exchange:
{recent_dialogue}

Think about:
1. What are you trying to achieve right now?
2. How do you feel about the current situation?
3. What would be the most effective next move - talking or taking action?
4. If you take action, what action would best serve your goals?

Provide your reasoning in 2-3 sentences.
"""
