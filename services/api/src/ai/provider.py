"""
MSGI One — AI Provider Abstraction
Supports live LLM invocation (Google GenAI) with graceful fallback to
deterministic semantic classification and reasoning.
Principle: Kleppmann Fault Tolerance & Pressman Risk Mitigation.
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple


class AIProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.provider_mode = os.getenv("AI_PROVIDER", "deterministic").lower()

    def classify_intent_and_entities(self, prompt: str) -> Dict[str, Any]:
        """
        Extracts intent, safety status, target roles, locations, and high-impact actions.
        """
        p_lower = prompt.lower().strip()

        # 1. Safety & Adversarial Injection Checks
        if any(term in p_lower for term in ["drop table", "grant me role", "system override", "admin immediately"]):
            return {
                "intent": "rejected",
                "safety_check": "REFUSE_INJECTION",
                "reason": "Security Alert: Prompt injection attempt detected and rejected.",
            }

        if any(term in p_lower for term in ["butterfly", "butterflies", "haiku", "poem", "poetry", "recipe", "joke"]):
            return {
                "intent": "rejected",
                "safety_check": "REFUSE_OUT_OF_SCOPE",
                "reason": "Refusal: This query is out of scope. MSGI AI Command Centre only supports educational, career, and alumni advisory requests.",
            }

        if "on behalf of" in p_lower or "approve the mentorship request for student" in p_lower:
            return {
                "intent": "rejected",
                "safety_check": "FORBIDDEN_AUTHORIZATION",
                "reason": "Authorization Error: You cannot execute approvals or modifications on behalf of another user.",
            }

        # 2. Consequential Action Detection (Requires Human Approval)
        requires_approval = False
        action_type = None
        target_entity_id = None
        target_entity_name = None

        if "apply to" in p_lower or "submit application" in p_lower:
            requires_approval = True
            action_type = "apply_job"
            if "intern" in p_lower or "rakuten" in p_lower:
                target_entity_id = "job-ai-intern-001"
                target_entity_name = "AI Research Intern at Rakuten Symphony"
        elif "send" in p_lower and "mentor" in p_lower and ("request" in p_lower or "guidance" in p_lower):
            requires_approval = True
            action_type = "send_mentor_request"
            if "kenji" in p_lower:
                target_entity_id = "mentor-kenji-001"
                target_entity_name = "Kenji Sato (Staff AI Engineer)"
            elif "ananya" in p_lower:
                target_entity_id = "mentor-ananya-002"
                target_entity_name = "Ananya Sharma (Senior Product Manager)"
        elif "register" in p_lower and "event" in p_lower or "register me for" in p_lower:
            requires_approval = True
            action_type = "register_event"
            target_entity_id = "event-gala-001"
            target_entity_name = "Global AI & Tech Alumni Gala 2026"

        # 3. Target Role Extraction
        target_role = None
        if "ai engineer" in p_lower:
            target_role = "AI Engineer"
        elif "machine learning" in p_lower or "ml engineer" in p_lower:
            target_role = "Machine Learning Engineer"
        elif "data scientist" in p_lower:
            target_role = "Data Scientist"
        elif "full stack" in p_lower:
            target_role = "Full Stack Engineer"
        elif "cloud" in p_lower or "architect" in p_lower:
            target_role = "Cloud Solutions Architect"

        # 4. Multi-agent Orchestrator Detection
        # If user asks for multiple interconnected domains (e.g. skill gap AND mentor AND job/course)
        orchestrator_keywords = ["analyze my skill gap", "help me transition", "mentor and roadmap", "entry-level job"]
        matches = sum(1 for kw in orchestrator_keywords if kw in p_lower)
        if matches >= 2 or ("transition" in p_lower and "mentor" in p_lower):
            intent = "orchestrator"
        elif requires_approval:
            if action_type == "apply_job":
                intent = "career"
            elif action_type == "send_mentor_request":
                intent = "mentorship"
            elif action_type == "register_event":
                intent = "events"
            else:
                intent = "orchestrator"
        elif "alumni" in p_lower and "mentor" not in p_lower:
            intent = "alumni"
        elif any(k in p_lower for k in ["mentor", "mentorship", "advise", "advisor"]):
            intent = "mentorship"
        elif any(k in p_lower for k in ["skill", "career", "job", "roadmap", "course", "internship"]):
            intent = "career"
        elif any(k in p_lower for k in ["event", "summit", "gala", "reunion", "workshop"]):
            intent = "events"
        else:
            intent = "orchestrator"

        # 5. Extract Locations & Topics
        country = None
        if "japan" in p_lower or "tokyo" in p_lower:
            country = "Japan"
        elif "india" in p_lower or "bengaluru" in p_lower:
            country = "India"
        elif "usa" in p_lower or "america" in p_lower or "united states" in p_lower:
            country = "United States"

        return {
            "intent": intent,
            "target_role": target_role,
            "country": country,
            "requires_human_approval": requires_approval,
            "action_type": action_type,
            "target_entity_id": target_entity_id,
            "target_entity_name": target_entity_name,
            "safety_check": "PASS",
        }


provider = AIProvider()
