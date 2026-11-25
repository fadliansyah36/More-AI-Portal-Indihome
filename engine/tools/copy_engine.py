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


def _decode_structured_copy_output(raw: str, *, mode: str, forbidden_claims: list[str]) -> str:
    """Validate the Copy Engine's promised structured response before it enters run output."""
    candidate = raw.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(candidate)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("copy_engine_output_not_valid_json") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("copy_engine_output_must_be_object")

    def nonempty_text(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    if not (nonempty_text(payload.get("brand_voice_spec")) or isinstance(payload.get("brand_voice_spec"), dict)):
        raise RuntimeError("copy_engine_output_brand_voice_spec_missing")
    if not nonempty_text(payload.get("core_message")):
        raise RuntimeError("copy_engine_output_core_message_missing")
    variants = payload.get("variants")
    if not isinstance(variants, list) or not 1 <= len(variants) <= 5:
        raise RuntimeError("copy_engine_output_variants_invalid")
    for index, variant in enumerate(variants):
        if not isinstance(variant, dict):
            raise RuntimeError(f"copy_engine_output_variant_{index}_invalid")
        if any(not nonempty_text(variant.get(field)) for field in ("label", "strategic_delta", "headline", "body", "channel_fit")):
            raise RuntimeError(f"copy_engine_output_variant_{index}_incomplete")
        if not (nonempty_text(variant.get("CTA")) or nonempty_text(variant.get("cta"))):
            raise RuntimeError(f"copy_engine_output_variant_{index}_cta_missing")
    for field in ("factual_gaps", "compliance_notes"):
        if not isinstance(payload.get(field), list) or any(not isinstance(item, str) for item in payload[field]):
            raise RuntimeError(f"copy_engine_output_{field}_invalid")
    if mode == "text_overlay":
        overlay = payload.get("media_overlay_spec")
        if not isinstance(overlay, dict) or overlay.get("renderer_status") != "spec_only":
            raise RuntimeError("copy_engine_output_overlay_spec_invalid")
        if not isinstance(overlay.get("missing_inputs"), list):
            raise RuntimeError("copy_engine_output_overlay_missing_inputs_invalid")

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    folded = serialized.casefold()
    if any(claim.casefold() in folded for claim in forbidden_claims if claim.strip()):
        raise RuntimeError("copy_engine_output_contains_forbidden_claim")
    return serialized


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
        media_context = text_field("media_context", 3000)
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
            "media_context": media_context,
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
                    "For mode text_overlay, also return media_overlay_spec with exact copy strings, text_template, "
                    "variable slots, font family/weight, color, alignment, canvas dimensions, bounding box, "
                    "overflow policy, missing_inputs and renderer_status=spec_only. Never invent canvas or brand "
                    "design values that are absent from media_context; list them as missing_inputs. This is a "
                    "specification only: do not claim that an image or video was rendered or composited. "
                    "Do not call tools or external providers. Source-derived workflow principles are adapted "
                    "from Scenario Skills scenario-brand-kit, scenario-ad-variants and scenario-text-overlay; "
                    "MoreAI implementation is an original adapter and imports no Scenario MCP, chevron, Pillow "
                    "or Chromium rendering dependencies."
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
        return _decode_structured_copy_output(
            output, mode=mode, forbidden_claims=forbidden_claims,
        )
