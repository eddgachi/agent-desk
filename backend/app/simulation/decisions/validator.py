"""
Validates LLM-generated decisions against simulation rules.

The hybrid engine checks decisions against these rules before
applying them. If a decision violates rules, the engine falls
back to the rule-based default.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def validate_decision(
    decision: str,
    reasoning: str,
    agent_id: str,
    agent_role: str,
    agent_energy: float,
    agent_focus: float,
    agent_status: str,
    current_task_id: Optional[str],
    conversation_partner_id: Optional[str],
) -> Dict:
    """
    Validate an LLM-generated decision.

    Returns a dict:
      - valid: bool — whether the decision passes all rules
      - reason: str — explanation of why it passed/failed
      - corrected_decision: str — fallback decision if invalid
    """
    # Rule 1: Don't override active conversations
    if conversation_partner_id and decision != "continue_current":
        return {
            "valid": False,
            "reason": "Agent is in a conversation; must continue_current",
            "corrected_decision": "continue_current",
        }

    # Rule 2: Don't take break if already on break
    if decision == "take_break" and agent_status == "break":
        return {
            "valid": False,
            "reason": "Agent is already on break",
            "corrected_decision": "wait",
        }

    # Rule 3: Don't socialize if energy too low (need to rest)
    if decision == "socialize" and agent_energy < 15:
        return {
            "valid": False,
            "reason": "Energy too low to socialize",
            "corrected_decision": "take_break",
        }

    # Rule 4: Don't take a break if energy is actually fine
    if decision == "take_break" and agent_energy > 60:
        # Walk it back to a softer suggestion
        logger.debug(
            "Agent %s wanted break but energy=%.0f is fine",
            agent_id, agent_energy,
        )
        return {
            "valid": True,
            "reason": "Energy is sufficient, but agent chose break (allowed)",
            "corrected_decision": decision,
        }

    # Rule 5: If focused on a task, prefer continue_current
    if decision != "continue_current" and current_task_id and agent_focus > 60:
        return {
            "valid": True,
            "reason": "Agent has active task but chose different action (allowed)",
            "corrected_decision": decision,
        }

    # All checks passed
    return {
        "valid": True,
        "reason": "Decision passes all validation rules",
        "corrected_decision": decision,
    }
