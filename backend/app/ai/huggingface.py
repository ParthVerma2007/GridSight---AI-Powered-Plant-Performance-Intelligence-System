import json
import httpx
from typing import Dict, Any, Optional
from app.ai.base import AIProvider
from app.ai.validator import AIResponseValidator
from app.schemas.ai import CompactContextPackage, AIExplanationResponse

class HuggingFaceProvider(AIProvider):
    def __init__(self, token: str, model_name: str = "meta-llama/Llama-3.2-3B-Instruct"):
        self.token = token
        self.model_name = model_name or "meta-llama/Llama-3.2-3B-Instruct"

    async def generate_explanation(
        self,
        context: CompactContextPackage
    ) -> AIExplanationResponse:
        """
        Calls Hugging Face Inference API with compact context package.
        """
        if not self.token:
            raise ValueError("HF_TOKEN is not configured.")

        system_instruction = (
            "You are the AI Energy Plant Intelligence Assistant for Helios-50 Solar Farm (50 MW). "
            "You strictly adhere to mathematical ground truth: NEVER hallucinate numerical values, NEVER invent causes, "
            "and ALWAYS distinguish between verified facts, supported explanations, hypotheses, and unknowns. "
            "Output ONLY valid JSON with keys: summary, verified_facts, supported_explanations, hypotheses, "
            "unknowns, strategic_or_operational_risks, recommended_actions, citations_and_evidence."
        )

        user_content = (
            f"USER ROLE: {context.user_role}\n"
            f"VERIFIED DETERMINISTIC METRICS:\n{json.dumps(context.verified_metrics)}\n\n"
            f"RECONCILED ATTRIBUTED CAUSES:\n{json.dumps(context.attributed_causes)}\n\n"
            f"EVENTS:\n{json.dumps(context.related_events)}\n\n"
            f"ALARMS:\n{json.dumps(context.equipment_alarms)}\n\n"
            f"QUESTION: {context.user_question or 'Generate performance intelligence summary'}\n\n"
            "Return JSON only."
        )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Use Hugging Face serverless inference API
        url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        payload = {
            "inputs": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_instruction}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n",
            "parameters": {
                "max_new_tokens": 1200,
                "temperature": 0.2,
                "return_full_text": False
            }
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Hugging Face API returned HTTP {resp.status_code}: {resp.text}")

            result = resp.json()
            if isinstance(result, list) and len(result) > 0:
                raw_text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                raw_text = result.get("generated_text", "") or str(result)
            else:
                raw_text = str(result)

        validated_resp, err = AIResponseValidator.validate_and_sanitize(
            raw_text,
            context,
            provider_name=f"huggingface:{self.model_name}"
        )

        if err or not validated_resp:
            raise ValueError(f"Hugging Face output validation failed: {err}")

        return validated_resp
