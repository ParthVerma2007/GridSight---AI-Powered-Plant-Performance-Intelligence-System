import logging
from typing import Optional
from app.config import settings
from app.schemas.ai import CompactContextPackage, AIExplanationResponse
from app.ai.base import AIProvider
from app.ai.gemini import GeminiProvider
from app.ai.huggingface import HuggingFaceProvider
from app.ai.fallback import DeterministicFallbackProvider

logger = logging.getLogger(__name__)

class AIService:
    """
    Central AI orchestration service.
    Configurable via environment variables (AI_PROVIDER=gemini | huggingface | fallback).
    Gracefully falls back to deterministic template generation if keys are missing,
    rate limits are hit, network timeouts occur, or validation fails.
    """

    def __init__(self):
        self.fallback_provider = DeterministicFallbackProvider()

    def get_provider(self, override_provider: Optional[str] = None) -> AIProvider:
        provider_name = (override_provider or settings.AI_PROVIDER).lower()

        if provider_name == "gemini":
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
                return GeminiProvider(
                    api_key=settings.GEMINI_API_KEY,
                    model_name=settings.GEMINI_MODEL
                )
            logger.info("GEMINI_API_KEY not configured. Falling back to deterministic engine.")
            return self.fallback_provider

        elif provider_name == "huggingface":
            if settings.HF_TOKEN and settings.HF_TOKEN.strip():
                return HuggingFaceProvider(
                    token=settings.HF_TOKEN,
                    model_name=settings.HF_MODEL
                )
            logger.info("HF_TOKEN not configured. Falling back to deterministic engine.")
            return self.fallback_provider

        return self.fallback_provider

    async def generate_explanation(
        self,
        context: CompactContextPackage,
        override_provider: Optional[str] = None
    ) -> AIExplanationResponse:
        """
        Executes AI explanation generation with automatic fallback on any error.
        """
        provider = self.get_provider(override_provider)

        try:
            return await provider.generate_explanation(context)
        except Exception as e:
            logger.warning(f"Active AI provider ({provider.__class__.__name__}) encountered error: {str(e)}. Triggering deterministic fallback.")
            fallback_resp = await self.fallback_provider.generate_explanation(context)
            fallback_resp.validation_status = f"fallback_template (reason: {str(e)[:120]})"
            return fallback_resp

ai_service = AIService()
