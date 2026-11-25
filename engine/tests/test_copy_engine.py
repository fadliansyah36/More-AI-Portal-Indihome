import json

import pytest

from engine.tools.copy_engine import _decode_structured_copy_output


def _valid_payload():
    return {
        "brand_voice_spec": {"tone": "clear", "style": "direct"},
        "core_message": "A factual product message",
        "variants": [{
            "label": "Primary",
            "strategic_delta": "Benefit-led",
            "headline": "A clear headline",
            "body": "A concise factual body",
            "CTA": "Learn more",
            "channel_fit": "Landing page",
        }],
        "factual_gaps": [],
        "compliance_notes": [],
    }


def test_copy_engine_accepts_structured_json_and_normalizes_fenced_response():
    payload = _valid_payload()
    raw = "```json\n" + json.dumps(payload) + "\n```"
    result = json.loads(_decode_structured_copy_output(raw, mode="headline", forbidden_claims=[]))
    assert result["variants"][0]["CTA"] == "Learn more"


def test_copy_engine_rejects_non_json_and_incomplete_variants():
    with pytest.raises(RuntimeError, match="not_valid_json"):
        _decode_structured_copy_output("Here is your copy", mode="headline", forbidden_claims=[])

    payload = _valid_payload()
    payload["variants"][0].pop("headline")
    with pytest.raises(RuntimeError, match="variant_0_incomplete"):
        _decode_structured_copy_output(json.dumps(payload), mode="headline", forbidden_claims=[])


def test_copy_engine_rejects_explicit_forbidden_claims():
    payload = _valid_payload()
    payload["variants"][0]["body"] = "Guaranteed results for everyone"
    with pytest.raises(RuntimeError, match="forbidden_claim"):
        _decode_structured_copy_output(
            json.dumps(payload), mode="headline",
            forbidden_claims=["Guaranteed results"],
        )


def test_copy_engine_text_overlay_requires_spec_only_renderer_contract():
    payload = _valid_payload()
    with pytest.raises(RuntimeError, match="overlay_spec_invalid"):
        _decode_structured_copy_output(
            json.dumps(payload), mode="text_overlay", forbidden_claims=[],
        )
    payload["media_overlay_spec"] = {"renderer_status": "spec_only", "missing_inputs": []}
    result = json.loads(_decode_structured_copy_output(
        json.dumps(payload), mode="text_overlay", forbidden_claims=[],
    ))
    assert result["media_overlay_spec"]["renderer_status"] == "spec_only"
