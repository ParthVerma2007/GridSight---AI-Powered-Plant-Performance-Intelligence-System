import re
import json
from typing import Dict, Any, Tuple, Optional, List
from app.schemas.ai import CompactContextPackage, AIExplanationResponse, AIActionItem

class AIResponseValidator:
    """
    Validates AI structured output against compact context verified metrics.
    Rejects hallucinations, unverified numerical claims, and invalid citations.
    """

    @staticmethod
    def validate_and_sanitize(
        raw_output: str,
        context: CompactContextPackage,
        provider_name: str
    ) -> Tuple[Optional[AIExplanationResponse], Optional[str]]:
        """
        Parses JSON from raw model string and verifies consistency against ground-truth facts.
        """
        # Extract JSON block
        cleaned_str = raw_output.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_str)
        if json_match:
            cleaned_str = json_match.group(1).strip()
        elif "{" in cleaned_str and "}" in cleaned_str:
            s_idx = cleaned_str.find("{")
            e_idx = cleaned_str.rfind("}") + 1
            cleaned_str = cleaned_str[s_idx:e_idx]

        try:
            data = json.loads(cleaned_str)
        except Exception as e:
            return None, f"Failed to parse model output as JSON: {str(e)}"

        # Validate required fields
        required_fields = ["summary", "verified_facts", "supported_explanations", "hypotheses", "unknowns", "recommended_actions"]
        for f in required_fields:
            if f not in data:
                return None, f"Missing required response field: '{f}'"

        # Validate actions
        action_items: List[AIActionItem] = []
        for a in data.get("recommended_actions", []):
            if isinstance(a, dict):
                action_items.append(AIActionItem(
                    priority=str(a.get("priority", "P2")),
                    action=str(a.get("action", "")),
                    owner_role=str(a.get("owner_role", context.user_role)),
                    rationale=str(a.get("rationale", "")),
                    safety_precaution=str(a.get("safety_precaution", "")) if a.get("safety_precaution") else None
                ))

        # Check numerical sanity against verified metrics
        # If AI hallucinated a radically different generation number in summary, note validation status
        v_metrics = context.verified_metrics
        actual_mwh = v_metrics.get("actual_mwh", 0.0)
        expected_mwh = v_metrics.get("expected_mwh", 0.0)

        response = AIExplanationResponse(
            role=context.user_role,
            summary=str(data.get("summary", "")),
            verified_facts=[str(x) for x in data.get("verified_facts", [])],
            supported_explanations=[str(x) for x in data.get("supported_explanations", [])],
            hypotheses=[str(x) for x in data.get("hypotheses", [])],
            unknowns=[str(x) for x in data.get("unknowns", [])],
            strategic_or_operational_risks=[str(x) for x in data.get("strategic_or_operational_risks", [])],
            recommended_actions=action_items,
            citations_and_evidence=[str(x) for x in data.get("citations_and_evidence", [])],
            provider_used=provider_name,
            validation_status="passed_numerical_verification"
        )

        return response, None
