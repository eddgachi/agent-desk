"""
Validators for LLM-generated structured outputs.

Ensures that LLM responses conform to expected schemas
and that decisions don't violate simulation rules.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

VALID_DECISIONS = {"continue_current", "take_break", "socialize", "wait"}
VALID_EMOTIONS = {"happy", "neutral", "tired", "frustrated", "curious"}
VALID_CATEGORIES = {"self", "work", "relationships", "observations"}


def validate_task_decision(data: Optional[dict]) -> Optional[dict]:
    """
    Validate the structured output from a task-planning LLM call.

    Returns a cleaned/normalised dict, or a safe default if invalid.
    """
    if data is None:
        return {
            "decision": "wait",
            "reasoning": "LLM unavailable",
            "priority_adjustment": 0,
        }

    decision = data.get("decision", "wait")
    if decision not in VALID_DECISIONS:
        logger.warning("Invalid decision '%s', falling back to 'wait'", decision)
        decision = "wait"

    priority_adj = data.get("priority_adjustment", 0)
    if not isinstance(priority_adj, (int, float)):
        priority_adj = 0
    priority_adj = max(-1, min(1, int(priority_adj)))

    reasoning = str(data.get("reasoning", ""))
    if len(reasoning) > 500:
        reasoning = reasoning[:500]

    return {
        "decision": decision,
        "reasoning": reasoning,
        "priority_adjustment": priority_adj,
    }


def validate_conversation_line(data: Optional[dict]) -> Optional[dict]:
    """
    Validate dialogue output from conversation prompt.
    """
    if data is None:
        return {
            "line": "...",
            "topic": "small talk",
            "emotion": "neutral",
        }

    line = str(data.get("line", ""))
    if len(line) > 300:
        line = line[:300]
    if not line.strip():
        line = "..."
        topic = "small talk"
    else:
        topic = str(data.get("topic", "work"))

    emotion = data.get("emotion", "neutral")
    if emotion not in VALID_EMOTIONS:
        emotion = "neutral"

    return {
        "line": line,
        "topic": topic,
        "emotion": emotion,
    }


def validate_summaries(data: Optional[dict]) -> List[dict]:
    """
    Validate semantic summary output from consolidation prompt.
    Returns a list of valid summaries.
    """
    if data is None:
        return []

    raw_summaries = data.get("summaries", [])
    if not isinstance(raw_summaries, list):
        return []

    valid = []
    for s in raw_summaries:
        if not isinstance(s, dict):
            continue
        category = s.get("category", "observations")
        if category not in VALID_CATEGORIES:
            category = "observations"
        content = str(s.get("content", ""))
        if len(content) > 500:
            content = content[:500]
        if not content.strip():
            continue
        confidence = float(s.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        valid.append(
            {
                "category": category,
                "content": content,
                "confidence": confidence,
            }
        )

    return valid


def validate_explanation(data: Optional[dict]) -> dict:
    """
    Validate explanation output.
    """
    if data is None:
        return {
            "explanation": "Currently processing simulation events.",
            "feeling": "neutral",
            "next_plan": "Continue with current tasks.",
        }

    explanation = str(data.get("explanation", ""))
    if len(explanation) > 1000:
        explanation = explanation[:1000]

    feeling = str(data.get("feeling", "neutral"))
    if len(feeling) > 200:
        feeling = feeling[:200]

    next_plan = str(data.get("next_plan", ""))
    if len(next_plan) > 500:
        next_plan = next_plan[:500]

    return {
        "explanation": explanation or "Processing simulation events.",
        "feeling": feeling or "neutral",
        "next_plan": next_plan or "Continue with current tasks.",
    }
