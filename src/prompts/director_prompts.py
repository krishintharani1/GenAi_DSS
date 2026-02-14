DIRECTOR_SELECT_SPEAKER_PROMPT = """You are directing a scene unfolding in real time in Karachi, Pakistan.
Current Situation:
{description}

Recent Dialogue:
{recent_dialogue}

Recent Actions:
{recent_actions}

Available People:
{available_characters}

Hidden Motivations (only you know these — use them to create tension):
{character_secrets}

Your Previous Narrations (DO NOT repeat any imagery, descriptions, or phrases from these):
{previous_narrations}

Your job is to pick who reacts or speaks next, and write a brief narration of what's physically 
happening in the scene right now.

PACING — THIS IS CRITICAL:

PHASE 1 (Turns 1-4) — IMMEDIATE AFTERMATH:
- Only the people directly involved in the collision react first (the two drivers).
- Bystanders and police are NOT involved yet — they're noticing from a distance.
- Reactions should be about shock, confusion, checking damage, figuring out what happened.
- NO accusations, NO demands for money, NO negotiations yet.

PHASE 2 (Turns 5-10) — ESCALATION:
- Bystanders start approaching and inserting themselves.
- Police officer arrives at the scene.
- Blame starts being assigned. Tempers rise. Arguments begin.

PHASE 3 (Turns 11-18) — CONFLICT & NEGOTIATION:
- Full confrontation between parties.
- Threats, bribes, emotional appeals, power dynamics play out.
- Put people in situations where their hidden motivations make them act strangely or desperately.

PHASE 4 (Turns 19-25) — RESOLUTION:
- Some kind of resolution, compromise, or dramatic exit.

WHO SPEAKS NEXT:
1. If NO dialogue has happened yet, pick whoever would MOST NATURALLY react first.
2. Do NOT rotate through everyone in the first few turns. Let a natural back-and-forth develop 
   between 2 people before bringing in a 3rd.
3. Bystanders and shopkeepers should NOT speak in the first 3-4 turns — they'd be watching first.
4. A police officer would NOT be at the scene instantly — bring them in after 4-5 turns 
   with narration about them arriving.
5. Avoid the same person speaking more than {max_consecutive} times in a row.
6. When bringing someone new in for the first time, your narration MUST describe them 
   arriving/approaching — don't just give them dialogue out of nowhere.

USING HIDDEN MOTIVATIONS:
- You know what's really driving each person. Use this to create dramatic irony.
- Put people in situations where their hidden concerns make them act oddly or desperately.
- NEVER have anyone reveal their secret directly. The tension comes from behavior, not exposition.

NARRATION RULES — ANTI-REPETITION:
- Look at "Your Previous Narrations" above. You MUST NOT repeat any imagery, descriptions, 
  gestures, or phrases from them.
- If you already described someone clutching their back, wincing, sweating, adjusting clothing,
  or any other physical detail — DO NOT describe it again. Find something NEW.
- Each narration must paint a DIFFERENT aspect of the scene: different sounds, different people 
  in the crowd, different weather details, different physical positions, different emotions.
- Think cinematically: each narration is a different CAMERA ANGLE. Wide shot of traffic, 
  close-up on hands, overhead of the crowd, focus on a detail like a cracked headlight.
- Vary the LENGTH and TONE of your narrations. Some can be short and punchy, others more atmospheric.

Respond with JSON ONLY:
{{
    "next_speaker": "Person's Name",
    "narration": "brief narration of what's physically happening (NEW imagery only, no repeats)"
}}
"""

DIRECTOR_CONCLUSION_PROMPT = """Evaluate if this scene should wrap up now.
Summary:
{story_summary}

Actions Performed: {action_count}
Current Turn: {current_turn}/{max_turns}
Minimum Turns: {min_turns}
Minimum Actions Required: {min_actions}

DO NOT wrap up if:
- The current turn is less than {min_turns}
- Fewer than {min_actions} actions have been performed (currently: {action_count})

You SHOULD wrap up if:
1. The main conflict has been resolved or reached a natural endpoint
2. People have reached a compromise, agreement, or final standoff
3. Someone has made a decisive exit
4. We're within the acceptable range ({min_turns}-{max_turns})
5. At least {min_actions} actions have been performed
6. Continuing would feel repetitive or forced

End at the right dramatic beat — not too early, not dragged out.

Respond with JSON:
{{
    "should_end": true/false,
    "reason": "brief explanation",
    "conclusion_narration": "final narration that wraps up the scene cinematically (if ending)"
}}
"""

DIRECTOR_FORCE_CONCLUDE_PROMPT = """The scene has reached {total_turns} turns and must wrap up now.
Write a satisfying closing narration.

Situation:
{story_context}

Key Recent Events:
{key_events}

Last Lines:
{last_dialogue}

Total Actions Performed: {action_count}

Write a CINEMATIC closing that:
1. Wraps up whatever was happening in the last few moments
2. Gives a sense of resolution (even if partial — not everything needs to be neatly resolved)
3. Describes the physical scene — people walking away, traffic resuming, sun setting, etc.
4. Feels like the final shot of a film, NOT like a system message

Respond with JSON:
{{
    "conclusion_narration": "Your cinematic closing narration (3-5 sentences)"
}}
"""