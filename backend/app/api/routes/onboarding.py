"""Company readiness assessment for the ArgusCX onboarding flow."""
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/onboarding")


class CompanyAssessmentRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    website: str | None = Field(default=None, max_length=300)
    industry: Literal["retail", "marketplace", "fintech", "logistics", "travel", "other"]
    support_platform: Literal["shopify", "woocommerce", "salesforce", "zendesk", "custom", "none"]
    primary_goal: Literal["returns", "fraud", "support_automation", "payment_disputes", "account_security"]
    monthly_volume: Literal["under_500", "500_5000", "5000_plus"]
    channels: list[Literal["email", "chat", "voice", "whatsapp", "web"]] = Field(default_factory=list, max_length=5)


class CompanyAssessmentResponse(BaseModel):
    summary: str
    data_required: list[str]
    integrations: list[str]
    launch_steps: list[str]
    risk_controls: list[str]
    ai_assisted: bool
    assessment_source: Literal["policy_baseline", "ai_refined"]


def _baseline_assessment(payload: CompanyAssessmentRequest) -> CompanyAssessmentResponse:
    goal_copy = {
        "returns": "verify return claims before money or replacement inventory is released",
        "fraud": "identify suspicious evidence, repeat patterns, and high-risk claims",
        "support_automation": "resolve routine support requests while sending complex cases to people",
        "payment_disputes": "investigate payment disputes with order and payment context",
        "account_security": "identify account-risk events and route them to a secure human review",
    }
    data_required = [
        "A stable customer or account identifier and consented contact channel.",
        "Case history, including status, category, and previous resolution outcomes.",
    ]
    integrations = []
    if payload.support_platform in {"shopify", "woocommerce"}:
        integrations.append("Read-only orders, fulfillment, catalog, and return-status access from the commerce platform.")
        data_required.append("Order number, SKU, delivery status, price, and return-window policy for each claim.")
    elif payload.support_platform in {"salesforce", "zendesk"}:
        integrations.append("Read-only ticket, customer, SLA, and agent-handoff access from the support platform.")
    elif payload.support_platform == "custom":
        integrations.append("A server-to-server webhook or REST adapter for cases, customers, and resolution updates.")
    else:
        integrations.append("Start with the ArgusCX REST API or CSV-backed pilot before connecting a support platform.")

    if payload.primary_goal in {"returns", "fraud"}:
        data_required.extend([
            "Original order and fulfillment data to compare with the claim.",
            "Customer-provided photos, video, or documents with declared retention rules.",
        ])
        integrations.append("Secure evidence upload and optional warehouse/outbound-image comparison.")
    if payload.primary_goal == "payment_disputes":
        data_required.append("Payment-provider dispute ID, transaction reference, amount, and payment status.")
        integrations.append("Read-only payment-provider connector or a signed payment-event webhook.")
    if payload.primary_goal == "account_security":
        data_required.append("Security events such as login anomalies, device changes, and recovery attempts.")
        integrations.append("Identity or security-event webhook with a least-privilege service account.")

    channel_label = ", ".join(payload.channels) if payload.channels else "your first chosen customer channel"
    review_rule = "Require a human decision for low-confidence or high-risk outcomes."
    if payload.monthly_volume == "5000_plus":
        review_rule = "Set queue ownership, escalation SLAs, and sampled quality review before high-volume rollout."

    return CompanyAssessmentResponse(
        summary=f"For {payload.company_name}, ArgusCX should first {goal_copy[payload.primary_goal]} across {channel_label}.",
        data_required=data_required,
        integrations=integrations,
        launch_steps=[
            "Map one case type and its resolution policy before enabling automation.",
            "Connect data with a read-only, server-side credential; never place provider secrets in a browser.",
            "Run a limited pilot, inspect case files with operators, then tune thresholds and expand coverage.",
        ],
        risk_controls=[
            "Minimize collected customer data and define evidence retention and deletion periods.",
            review_rule,
            "Keep an audit record of AI recommendations, human overrides, and outbound actions.",
        ],
        ai_assisted=False,
        assessment_source="policy_baseline",
    )


async def _refine_summary_with_llm(payload: CompanyAssessmentRequest, baseline: CompanyAssessmentResponse) -> str | None:
    """Use the configured LLM only for an authenticated, non-secret summary refinement."""
    if not settings.GROQ_API_KEY:
        return None
    try:
        from app.core.llm import get_llm

        llm = get_llm(temperature=0.1)
        if not llm:
            return None
        prompt = (
            "Write one concise onboarding recommendation for an AI customer-support platform. "
            "Do not invent integrations, guarantees, legal advice, or credentials. "
            f"Company: {payload.company_name}. Industry: {payload.industry}. Goal: {payload.primary_goal}. "
            f"Platform: {payload.support_platform}. Volume: {payload.monthly_volume}. "
            f"Approved baseline: {baseline.summary}"
        )
        result = await llm.ainvoke(prompt)
        text = getattr(result, "content", "")
        return text.strip()[:700] if isinstance(text, str) and text.strip() else None
    except Exception:
        # The baseline is intentionally complete when an LLM is unavailable.
        return None


@router.post("/assessment", response_model=CompanyAssessmentResponse)
async def assess_company_readiness(payload: CompanyAssessmentRequest, request: Request):
    """Produce a practical integration plan without collecting provider secrets."""
    baseline = _baseline_assessment(payload)
    # Anonymous visitors receive a complete policy baseline. Authenticated
    # dashboard users may receive an optional LLM-refined wording.
    if getattr(request.state, "auth_type", None) == "dashboard_jwt":
        refined_summary = await _refine_summary_with_llm(payload, baseline)
        if refined_summary:
            baseline.summary = refined_summary
            baseline.ai_assisted = True
            baseline.assessment_source = "ai_refined"
    return baseline
