import pytest
from app.ai.fallback import DeterministicFallbackProvider
from app.ai.validator import AIResponseValidator
from app.ai.service import AIService
from app.schemas.ai import CompactContextPackage, AIExplanationResponse

@pytest.mark.asyncio
async def test_fallback_provider_works_without_credentials():
    provider = DeterministicFallbackProvider()

    context = CompactContextPackage(
        user_role="OPERATIONS",
        plant_id="helios-50",
        plant_name="Helios-50 Solar Farm",
        period_start="2026-10-18T00:00:00",
        period_end="2026-10-19T00:00:00",
        verified_metrics={
            "expected_mwh": 280.0,
            "actual_mwh": 240.0,
            "variance_mwh": -40.0,
            "variance_pct": -14.3,
            "availability_pct": 96.5,
            "lost_revenue_usd": 1940.0,
            "realized_revenue_usd": 11640.0,
            "ppa_tariff_usd_per_mwh": 48.50
        },
        attributed_causes=[
            {
                "category": "equipment_fault",
                "title": "Inverter 04 Thermal Trip",
                "loss_mwh": 25.0,
                "loss_usd": 1212.50,
                "recurrence": "recurring",
                "evidence": []
            }
        ],
        related_events=[],
        equipment_alarms=[],
        financial_parameters={"ppa_tariff": 48.50}
    )

    resp = await provider.generate_explanation(context)
    assert isinstance(resp, AIExplanationResponse)
    assert resp.role == "OPERATIONS"
    assert len(resp.verified_facts) > 0
    assert len(resp.supported_explanations) > 0
    assert len(resp.hypotheses) > 0
    assert len(resp.unknowns) > 0
    assert len(resp.recommended_actions) > 0

@pytest.mark.asyncio
async def test_ai_service_graceful_fallback():
    # AIService with invalid provider or missing credentials must smoothly fallback
    service = AIService()
    context = CompactContextPackage(
        user_role="CEO",
        plant_id="helios-50",
        plant_name="Helios-50 Solar Farm",
        period_start="2026-10-18T00:00:00",
        period_end="2026-10-19T00:00:00",
        verified_metrics={"expected_mwh": 100.0, "actual_mwh": 90.0, "variance_mwh": -10.0, "lost_revenue_usd": 485.0},
        attributed_causes=[],
        related_events=[],
        equipment_alarms=[],
        financial_parameters={"ppa_tariff": 48.50}
    )

    resp = await service.generate_explanation(context, override_provider="gemini")
    assert resp.role == "CEO"
    assert "revenue" in resp.summary.lower() or "generation" in resp.summary.lower()

def test_response_validator_rejects_malformed_json():
    context = CompactContextPackage(
        user_role="OPERATIONS",
        plant_id="helios-50",
        plant_name="Helios-50 Solar Farm",
        period_start="2026-10-18T00:00:00",
        period_end="2026-10-19T00:00:00",
        verified_metrics={},
        attributed_causes=[],
        related_events=[],
        equipment_alarms=[],
        financial_parameters={}
    )

    bad_json = "THIS IS NOT JSON AND CONTAINS NO BRACKETS"
    resp, err = AIResponseValidator.validate_and_sanitize(bad_json, context, "test_provider")
    assert resp is None
    assert err is not None
