from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas.ai import CompactContextPackage, AIExplanationResponse

class AIProvider(ABC):
    @abstractmethod
    async def generate_explanation(
        self,
        context: CompactContextPackage
    ) -> AIExplanationResponse:
        """
        Generates a structured, evidence-grounded AI explanation based on
        the compact context package and role profile.
        """
        pass
