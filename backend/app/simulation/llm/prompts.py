"""
Structured prompt templates for DeepSeek LLM calls.

Each prompt template is a function that returns a list of messages
suitable for passing to DeepSeekClient.chat() or chat_structured().

Templates:
  - TASK_PLANNING:   Agent decides what to do next (bounded by rules)
  - CONVERSATION:    Generate dialogue between two chatting agents
  - SUMMARIZATION:   Summarize episodic memory into semantic summaries
  - EXPLANATION:     Explain an agent's recent actions (for UI display)
"""

from typing import Dict, List


def build_system_prompt(agent_name: str, role: str) -> str:
    """Base system prompt establishing role and constraints."""
    return (
        f"You are {agent_name}, a {role} in a tech office simulation. "
        "You have internal stats (energy 0-100, focus 0-100, mood 0-100) "
        "that affect your behaviour. You work on tasks, attend meetings, "
        "chat with colleagues, and take breaks when needed.\n\n"
        "Rules:\n"
        "1. Your responses influence your character's decisions only within "
        "the bounds of the simulation engine.\n"
        "2. Always respond in character as a professional office worker.\n"
        "3. Be concise — your reply will be used in a real-time simulation.\n"
        "4. You cannot refuse assigned tasks, but you can suggest priorities."
    )


def build_task_planning_prompt(
    agent_name: str,
    role: str,
    stats: Dict[str, float],
    current_context: str,
) -> List[Dict[str, str]]:
    """
    Prompt the agent to decide what to focus on next.

    Returns a list of messages for the LLM API.
    The response format is JSON with fields:
      - decision: "continue_current" | "take_break" | "socialize" | "wait"
      - reasoning: short explanation
      - priority_adjustment: -1, 0, or +1 (optional priority modification)
    """
    system = build_system_prompt(agent_name, role)

    user = (
        f"Current tick context:\n{current_context}\n\n"
        f"Your stats:\n"
        f"  Energy: {stats.get('energy', 100):.0f}/100\n"
        f"  Focus:  {stats.get('focus', 100):.0f}/100\n"
        f"  Mood:   {stats.get('mood', 100):.0f}/100\n\n"
        "Given your current situation, what should you do?\n"
        'Respond with JSON: {"decision": "...", "reasoning": "...", '
        '"priority_adjustment": 0}\n'
        "decision options: continue_current, take_break, socialize, wait"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_conversation_prompt(
    agent_a: str,
    role_a: str,
    agent_b: str,
    role_b: str,
    recent_context: str,
) -> List[Dict[str, str]]:
    """
    Generate a line of dialogue from agent_a to agent_b.

    Returns JSON with fields:
      - line: the dialogue text
      - topic: what they're talking about
      - emotion: happy | neutral | tired | frustrated | curious
    """
    system = (
        f"You are {agent_a}, a {role_a} in a tech office. "
        f"You are chatting with {agent_b} ({role_b}). "
        "Keep conversation natural, work-appropriate, and concise "
        "(1-2 sentences). Respond in character."
    )

    user = (
        f"Recent context:\n{recent_context}\n\n"
        f"Generate a line of dialogue from {agent_a} to {agent_b}.\n"
        'Respond with JSON: {"line": "...", "topic": "...", '
        '"emotion": "neutral"}'
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_summarization_prompt(
    agent_name: str,
    recent_episodes: str,
) -> List[Dict[str, str]]:
    """
    Consolidate episodic memory entries into semantic summaries.

    Returns JSON with fields:
      - summaries: list of {"category": "...", "content": "...", "confidence": 0.0-1.0}
    """
    system = (
        f"You are {agent_name}'s internal memory consolidation system. "
        "Your job is to summarise recent events into lasting knowledge. "
        "Categories: self (who I am, my traits), work (tasks, projects), "
        "relationships (other agents), observations (general). "
        "Be concise — each summary is 1-2 sentences."
    )

    user = (
        f"Recent events to consolidate:\n{recent_episodes}\n\n"
        "Generate semantic summaries from these events.\n"
        'Respond with JSON: {"summaries": [{"category": "...", '
        '"content": "...", "confidence": 0.8}]}'
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_explanation_prompt(
    agent_name: str,
    role: str,
    recent_actions: str,
    stats: Dict[str, float],
) -> List[Dict[str, str]]:
    """
    Generate a natural-language explanation of the agent's recent behaviour
    (shown in the UI inspector panel).

    Returns JSON with fields:
      - explanation: 1-3 sentence explanation
      - feeling: how the agent feels right now
      - next_plan: what they plan to do next (vague is okay)
    """
    system = build_system_prompt(agent_name, role)

    user = (
        f"Recent actions:\n{recent_actions}\n\n"
        f"Your stats:\n"
        f"  Energy: {stats.get('energy', 100):.0f}/100\n"
        f"  Focus:  {stats.get('focus', 100):.0f}/100\n"
        f"  Mood:   {stats.get('mood', 100):.0f}/100\n\n"
        "Explain what you're doing and why, as if narrating to an observer.\n"
        'Respond with JSON: {"explanation": "...", '
        '"feeling": "...", "next_plan": "..."}'
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
