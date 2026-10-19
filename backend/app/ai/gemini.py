import json
import httpx
from typing import Dict, Any, Optional
from app.ai.base import AIProvider
from app.ai.validator import AIResponseValidator
from app.schemas.ai import CompactContextPackage, AIExplanationResponse
from app.config import settings

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name or "gemini-2.5-flash"

    async def generate_explanation(
        self,
        context: CompactContextPackage
    ) -> AIExplanationResponse:
        """
        Calls Gemini API with compact context package and enforces structured JSON response.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        system_instruction = (
            "You are the AI Energy Plant Intelligence Architect for Helios-50 Solar Farm (50 MW). "
            "You strictly adhere to mathematical ground truth: NEVER hallucinate numerical values, NEVER invent causes, "
            "and ALWAYS distinguish between verified facts, supported explanations, hypotheses, and unknowns. "
            "Tailor your response specifically for the requested user role. "
            "Output ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "summary": "...",\n'
            '  "verified_facts": ["..."],\n'
            '  "supported_explanations": ["..."],\n'
            '  "hypotheses": ["..."],\n'
            '  "unknowns": ["..."],\n'
            '  "strategic_or_operational_risks": ["..."],\n'
            '  "recommended_actions": [{"priority": "P1|P2|P3", "action": "...", "owner_role": "...", "rationale": "...", "safety_precaution": "..."}],\n'
            '  "citations_and_evidence": ["..."]\n'
            "}"
        )

        user_prompt = (
            f"USER ROLE: {context.user_role}\n"
            f"PLANT: {context.plant_name} (50 MW)\n"
            f"ANALYSIS PERIOD: {context.period_start} to {context.period_end}\n"
            f"USER QUESTION: {context.user_question or 'Provide comprehensive role-based plant performance intelligence and root-cause analysis.'}\n\n"
            f"VERIFIED DETERMINISTIC METRICS:\n{json.dumps(context.verified_metrics, indent=2)}\n\n"
            f"RECONCILED ATTRIBUTED CAUSES & EVIDENCE:\n{json.dumps(context.attributed_causes, indent=2)}\n\n"
            f"RELATED EVENTS (Grid/Weather):\n{json.dumps(context.related_events, indent=2)}\n\n"
            f"EQUIPMENT ALARMS & TELEMETRY:\n{json.dumps(context.equipment_alarms, indent=2)}\n\n"
            f"FINANCIAL PARAMETERS:\n{json.dumps(context.financial_parameters, indent=2)}\n\n"
            "Respond ONLY with the structured JSON object."
        )

        # Call Gemini API via Google GenAI REST endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_instruction}\n\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")

            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidates returned from Gemini API")

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        validated_resp, err = AIResponseValidator.validate_and_sanitize(
            raw_text,
            context,
            provider_name=f"gemini:{self.model_name}"
        )

        if err or not validated_resp:
            raise ValueError(f"Gemini output validation failed: {err}")

        return validated_resp
