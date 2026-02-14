# GenAI_DSS: Multi-Agent Narrative System

## 1. Introduction
This repository serves as the **complete implementation** for the **Generative AI module of the Hackfest x Datathon**.

The system implements a **Multi-Agent Narrative System** where autonomous agents navigate a world defined by a "Story Seed." The agents possess:
- **Character Memory**: Individual memory buffers tracking observations, inventory, goals, and perceptions
- **Reasoning Layer**: Agents think through their goals and decide whether to talk or act
- **Action System**: Non-verbal behaviors that modify the story state
- **Physical Presence**: Agents can perform actions like leaving, searching, giving items, etc.

This implementation uses **LangGraph** to orchestrate agentic flow, character interaction, and director oversight.

## 2. Setup

This project uses `uv` for dependency management.

### Prerequisites
- Python 3.11+
- `uv` package manager
- Google Gemini API Key (free tier available)

### Installation

1.  **Fork the repository**:
    - Go to the repository page on GitHub.
    - Click the **Fork** button in the top-right corner to create your own copy.
    - Clone *your forked repository*:
      ```bash
      git clone https://github.com/YOUR_USERNAME/GenAi_DSS.git
      cd GenAi_DSS
      ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

3.  **Environment Configuration**:
    Create a `.env` file in the root directory and add your Google API Key:
    ```ini
    GOOGLE_API_KEY=your_api_key_here
    ```

## 3. System Architecture

The system is built on a modular architecture to simulate a narrative environment.

### Core Components

- **The Director (`DirectorAgent`)**:
    - Acts as the central controller.
    - Decides which character speaks next based on the narrative context.
    - Monitors the story for conclusion conditions.
    - Tracks action count to ensure minimum 5 actions are performed.
    - Injects narrations to guide the plot.

- **Character Agents (`CharacterAgent`)**:
    - Distinct personas defined in `character_configs.json`.
    - Generate dialogue OR perform actions based on their goals and reasoning.
    - Maintain individual memory buffers with observations, inventory, goals, and perceptions.
    - Use a reasoning layer to decide when to talk vs. when to act.

- **Character Memory System**:
    - Each character has an individual `CharacterMemory` buffer.
    - Tracks:
        - **Observations**: What they've seen and heard
        - **Inventory**: Items they possess
        - **Goals**: Current objectives
        - **Perceptions**: How they view other characters
        - **Important Facts**: Key information to remember

- **Action System**:
    - Characters can perform non-verbal actions that modify the story state.
    - Available actions:
        - `LEAVE`: Leave the current location
        - `SEARCH`: Search for objects or information
        - `GIVE`: Give an item to another character
        - `TAKE`: Take an item
        - `CALL`: Make a phone call
        - `SHOW`: Show something to someone
        - `THREATEN`: Make a threatening gesture
        - `GESTURE`: Make a significant non-verbal gesture
        - `MOVE`: Move to a different position
    - Actions have effects that update the world state
    - Minimum 5 actions required per story

- **Reasoning Layer**:
    - Characters think through their goals before responding
    - JSON-formatted responses include reasoning explanation
    - Decision logic for choosing between dialogue and action
    - Ensures actions are purposeful and goal-driven

- **Story State Manager (`StoryStateManager`)**:
    - Centralized state management for the simulation.
    - Tracks the story progression, including dialogue history and action history.
    - Provides context-aware state views for both the Director and Character agents.
    - Manages turn counting and checks for story conclusion conditions.
    - Maintains world state (locations, character presence, etc.)

- **Narrative Graph (`NarrativeGraph`)**:
    - The state machine that orchestrates the flow of the simulation.
    - Built using `LangGraph`.
    - Manages the loop: `Director Selects` -> `Character Responds (Talk or Act)` -> `Check Conclusion`.

## 4. System Architecture Diagram

The following diagram illustrates the flow of the system:

![Narrative Graph](narrative_graph.png)

## 5. Usage

> [!IMPORTANT]
> **Mandatory Seed Story**: All participants **MUST** use the provided "Rickshaw Accident" seed story (`examples/rickshaw_accident/seed_story.json`) for their submission.

To run the simulation:

```bash
uv run src/main.py
```

The system will:
1. Load the seed story and character configurations.
2. Initialize the agents with memory buffers.
3. Run the dialogue/action loop for a maximum of 25 turns.
4. Ensure at least 5 actions are performed.
5. Save the story transcript and logs.

### Output Files

Your system generates the following output files:

**1. Narration Output (`story_output.json`)**
This file records the final narrative trace of the simulation. It contains:
- **Metadata**: Title, seed story description, total turns, total actions.
- **Events**: A chronological list of turns, including:
    - `type`: "dialogue", "action", or "narration".
    - `speaker`/`actor`: Who spoke or acted.
    - `content`: The actual text generated.
    - `turn`: The turn number.
    - `action_type`: Type of action (if applicable).
- **Conclusion**: Why the story ended.

**2. Prompts Log (`prompts_log.json`)**
This file serves as a debug/audit log for the LLM interactions. It tracks:
- `timestamp`: When the request was made.
- `agent`: Which agent (Director or Character) made the request.
- `prompt`: The full text prompt sent to the LLM.
- `response`: The raw response received from the model.

## 6. Implementation Details

### Character Memory

Each character maintains an individual memory buffer that includes:

```python
class CharacterMemory:
    character_name: str
    observations: List[str]        # What they've observed
    inventory: List[str]           # Items they possess
    goals: List[str]               # Current goals
    perceptions: Dict[str, str]    # Perceptions of others
    important_facts: List[str]     # Key facts to remember
```

Memory is automatically updated when:
- A character speaks (they remember what they said)
- A character performs an action (they remember their action)
- Another character performs an action (they observe it)

### Action System

Actions are structured as:

```python
class Action:
    turn_number: int
    actor: str
    action_type: str               # The type of action
    target: Optional[str]          # Target of action
    description: str               # Narrative description
    effects: Dict[str, Any]        # State changes
```

Actions can modify:
- World state (e.g., characters present, tension level)
- Character inventories
- Location state

### Reasoning Layer

Characters use a JSON response format:

```json
{
    "reasoning": "Why I'm choosing this response",
    "action_type": "TALK" or an action type,
    "action_target": "target if action",
    "response": "dialogue or action description"
}
```

This ensures characters think before acting and provides transparency into their decision-making.

## 7. Configuration

Key parameters in `src/config.py`:

- `max_turns`: 25 (Maximum dialogue turns)
- `min_turns`: 10 (Minimum turns before conclusion)
- `max_tokens_per_prompt`: 2000 (Max tokens per LLM generation)
- `max_context_length`: 4000 (Max context window)
- `temperature`: 0.7 (Adjustable for creativity vs. consistency)
- `model_name`: ""gemma-3-27b-it"" (Google Gemini model)

## 8. Key Features Implemented

✅ **Character Memory**: Individual memory buffers for each character
✅ **Action System**: 9 types of non-verbal actions that modify story state
✅ **Reasoning Layer**: Characters think through goals before responding
✅ **Turn Management**: Strict 25-turn limit
✅ **Action Tracking**: Ensures minimum 5 actions are performed
✅ **World State**: Tracks global state including locations and character presence
✅ **Event Logging**: Comprehensive event log for story reconstruction
✅ **Prompt Logging**: Full audit trail of LLM interactions

## 9. Example Character Configuration

```json
{
    "name": "Saleem",
    "description": "Poor rickshaw driver, sole earner for family of 5...",
    "initial_inventory": ["rickshaw", "driver's license", "500 rupees"],
    "initial_goals": ["avoid paying damages", "keep license", "get home to family"]
}
```

## 10. Troubleshooting

**Issue**: "ModuleNotFoundError"
**Solution**: Run `uv sync` to install dependencies

**Issue**: "GOOGLE_API_KEY not found"
**Solution**: Create `.env` file with your API key

**Issue**: "Story ends with fewer than 5 actions"
**Solution**: The system will warn you. The director is configured to prevent early conclusion if action count is low.

## 11. License

This project is for educational purposes as part of the Hackfest x Datathon challenge.
