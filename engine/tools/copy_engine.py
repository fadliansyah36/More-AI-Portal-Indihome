from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol


class MeteredTextGateway(Protocol):
    async def complete(
        self, *, user_id: str, run_id: str, request_key: str,
        messages: list[dict[str, Any]], task_type: str = "chat",
        workspace_id: str | None = None, partner_id: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        required_capabilities: set[str] | None = None,
    ) -> dict[str, Any]: ...


class CopyEngineAdapter:
    """MoreAI-native copy generation on the existing metered OpenManus gateway.

    Workflow patterns are adapted from Scenario Skills (MIT):
    - scenario-brand-kit: write a compact brand/voice specification before copy.
    - scenario-ad-variants: keep variant deltas explicit and preserve shared invariants.
    No Scenario MCP, remote model, or external provider is called.
    """

    MODES = {
        "brand_voice", "campaign_concept", "ad_variant", "social_caption",
        "landing_page", "product_description", "email", "headline", "text_overlay",
    }

    def __init__(self, gateway: MeteredTextGateway):
        self.gateway = gateway

    async def generate(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        mode = arguments.get("mode", "campaign_concept")
        brief = arguments.get("brief")
        if mode not in self.MODES:
            raise ValueError("copy_engine_mode_not_supported")
        if not isinstance(brief, str) or not brief.strip() or len(brief) > 12000:
            raise ValueError("copy_engine_brief_invalid")

        def text_field(name: str, limit: int) -> str:
            value = arguments.get(name, "")
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError(f"copy_engine_{name}_invalid")
            return value.strip()

        def string_list(name: str, maximum: int, item_limit: int) -> list[str]:
            value = arguments.get(name, [])
            if not isinstance(value, list) or len(value) > maximum:
                raise ValueError(f"copy_engine_{name}_invalid")
            if any(not isinstance(item, str) or not item.strip() or len(item) > item_limit for item in value):
                raise ValueError(f"copy_engine_{name}_invalid")
            return [item.strip() for item in value]

        locale = text_field("locale", 40) or "id-ID"
        audience = text_field("audience", 1200)
        product = text_field("product_context", 3000)
        brand = text_field("brand_context", 3000)
        voice = text_field("brand_voice", 1200)
        channels = string_list("channels", 8, 80)
        constraints = string_list("constraints", 20, 500)
        source_facts = string_list("source_facts", 30, 1000)
        forbidden_claims = string_list("forbidden_claims", 30, 500)
        variants = arguments.get("variants", 3)
        if isinstance(variants, bool) or not isinstance(variants, int) or not 1 <= variants <= 5:
            raise ValueError("copy_engine_variants_invalid")

        brief_data = {
            "mode": mode,
            "locale": locale,
            "brief": brief.strip(),
            "audience": audience,
            "product_context": product,
            "brand_context": brand,
            "brand_voice": voice,
            "channels": channels,
            "constraints": constraints,
            "source_facts": source_facts,
            "forbidden_claims": forbidden_claims,
            "variants": variants,
        }
        payload_hash = hashlib.sha256(
            json.dumps(brief_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are MoreAI Copy Engine, a professional brand and conversion copywriter. "
                    "Return polished, original copy in the requested locale. Start by inferring a concise "
                    "brand/voice specification from supplied facts; distinguish confirmed facts from assumptions. "
                    "Never invent prices, discounts, guarantees, certifications, performance, customer results, "
                    "legal claims, scarcity, testimonials, or product capabilities. If a fact is missing, omit it "
                    "or label the gap clearly. Do not make deceptive, discriminatory, manipulative, or unsupported "
                    "claims. Respect the exact channel, audience, constraints and forbidden claims. "
                    "For variants, keep the shared facts and positioning invariant; state the one intentional "
                    "creative delta for each variant and do not create a Cartesian combination. "
                    "Return a compact structured result with: brand_voice_spec, core_message, variants "
                    "(label, strategic_delta, headline, body, CTA, channel_fit), factual_gaps, and compliance_notes. "
                    "Do not call tools or external providers. Source-derived workflow principles are adapted "
                    "from Scenario Skills scenario-brand-kit and scenario-ad-variants; MoreAI implementation "
                    "is an original adapter and uses no Scenario MCP."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(brief_data, ensure_ascii=False, separators=(",", ":")),
            },
        ]
        result = await self.gateway.complete(
            user_id=user_id,
            run_id=run_id,
            request_key=f"{run_id}:copy-engine:{payload_hash}",
            messages=messages,
            task_type="chat",
        )
        output = result.get("text")
        if not isinstance(output, str) or not output.strip():
            raise RuntimeError("copy_engine_empty_provider_response")
        return output
