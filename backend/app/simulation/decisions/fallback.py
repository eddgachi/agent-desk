"""
Fallback strategies for when the LLM is unavailable, rate-limited,
or produces invalid output.

Each fallback is a deterministic rule-based decision that preserves
simulation continuity.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def fallback_task_decision(
    agent_id: str,
    agent_energy: float,
    agent_focus: float,
    agent_mood: float,
    has_active_task: bool,
    conversation_partner_id: Optional[str],
    current_tick: int,
    last_break_tick: int,
    break_cooldown: int = 30,
) -> Dict:
    """
    Deterministic fallback when LLM task planning is unavailable.

    Returns the same structure as validate_task_decision.
    """
    # If in conversation, continue
    if conversation_partner_id:
        return {
            "decision": "continue_current",
            "reasoning": "Currently in a conversation.",
            "priority_adjustment": 0,
        }

    # If actively working, continue
    if has_active_task and agent_focus > 30:
        return {
            "decision": "continue_current",
            "reasoning": "Focusing on assigned task.",
            "priority_adjustment": 0,
        }

    # If energy critically low and cooldown OK, take break
    cooldown_ok = (current_tick - last_break_tick) >= break_cooldown
    if agent_energy < 20 and cooldown_ok:
        return {
            "decision": "take_break",
            "reasoning": f"Energy critically low ({agent_energy:.0f}/100).",
            "priority_adjustment": 0,
        }

    # If moderately low energy, consider break
    if agent_energy < 35 and cooldown_ok and agent_focus < 40:
        return {
            "decision": "take_break",
            "reasoning": f"Energy ({agent_energy:.0f}) and focus ({agent_focus:.0f}) declining.",
            "priority_adjustment": 0,
        }

    # If mood is high and idle, consider socializing
    if agent_mood > 70 and not has_active_task:
        return {
            "decision": "socialize",
            "reasoning": "Feeling sociable while idle.",
            "priority_adjustment": 0,
        }

    # Default: wait for new tasks
    return {
        "decision": "wait",
        "reasoning": "Awaiting new task assignments.",
        "priority_adjustment": 0,
    }


def fallback_conversation_line(
    agent_name: str,
    partner_name: str,
    topic: Optional[str] = None,
) -> Dict:
    """Generate a simple rule-based conversation line."""
    greetings = [
        "Hey, how's it going?",
        "Good to see you!",
        "How's your day going?",
        "Hey there!",
    ]
    work_topics = [
        "How's that task coming along?",
        "Have you seen the latest updates?",
        "Let me know if you need any help.",
        "I've been working on that project too.",
    ]

    import random

    rng = random.Random()
    rng.seed(hash(f"{agent_name}-{partner_name}-{topic}") % (2**32))

    line = rng.choice(work_topics) if topic else rng.choice(greetings)

    return {
        "line": line,
        "topic": topic or "general",
        "emotion": "neutral",
    }


def fallback_explanation(
    agent_name: str,
    role: str,
    status: str,
    energy: float,
    focus: float,
) -> Dict:
    """Generate a simple explanation based on current state."""
    if status == "working":
        explanation = "I'm focused on my current task."
    elif status == "moving":
        explanation = "I'm on my way to a destination."
    elif status == "break":
        explanation = "I'm taking a short break to recharge."
    elif status == "chatting":
        explanation = "I'm having a chat with a colleague."
    elif status == "meeting":
        explanation = "I'm in a meeting right now."
    else:
        explanation = "I'm available and waiting for the next task."

    if energy < 30:
        feeling = "tired"
    elif energy < 60:
        feeling = "neutral"
    else:
        feeling = "okay"

    return {
        "explanation": explanation,
        "feeling": feeling,
        "next_plan": "Continue working or take appropriate action.",
    }
