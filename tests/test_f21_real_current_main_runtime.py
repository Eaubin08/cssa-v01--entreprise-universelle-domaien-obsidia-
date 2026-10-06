import os
import sys
from pathlib import Path

import pytest

from universal.contracts.domain_v0 import GovernancePayloadV0
from universal.integration.main_runtime_v0 import (
    UnsupportedCurrentMainDomain,
    current_main_supported_domains,
    decide_with_real_current_main_guard,
    governance_payload_to_real_upstream_aggregate,
)


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))


def payload(
    domain_id: str,
    *,
    unknowns=(),
    contradictions=(),
    risk_flags=(),
) -> GovernancePayloadV0:
    return GovernancePayloadV0(
        domain_id=domain_id,
        domain_state_ref=f"{domain_id}:state:1",
        upstream_state_ref="source:fixture:1",
        unknowns=tuple(unknowns),
        contradictions=tuple(contradictions),
        risk_flags=tuple(risk_flags),
        evidence_refs=("evidence:1",),
        provenance_refs=("upstream-main",),
        proposed_action_ref=f"proposal:{domain_id}",
    )


def test_reads_real_current_main_governed_runtime_domain_table():
    domains = set(current_main_supported_domains(UPSTREAM))
    assert {"bank", "trading", "ecom", "gps_defense_aviation"} <= domains
    assert "administration" not in domains


@pytest.mark.parametrize(
    "domain_id",
    ["bank", "trading", "ecom", "gps_defense_aviation"],
)
def test_f1_payload_reaches_real_current_main_guard(domain_id):
    envelope = decide_with_real_current_main_guard(
        payload(domain_id),
        source_root=UPSTREAM,
        confidence=0.90,
    )

    # Real upstream object and real upstream sovereign decision surface.
    from sigma.contracts import CanonicalDecisionEnvelope

    assert isinstance(envelope, CanonicalDecisionEnvelope)
    assert envelope.domain == domain_id
    assert envelope.x108_gate in {"ALLOW", "HOLD", "BLOCK"}
    assert envelope.decision_id
    assert envelope.trace_id
    assert envelope.source == "canonical_framework"


def test_real_guard_produces_allow_from_clean_payload_not_from_domain():
    envelope = decide_with_real_current_main_guard(
        payload("bank"),
        source_root=UPSTREAM,
        confidence=0.90,
    )
    assert envelope.market_verdict == "HOLD"
    assert envelope.x108_gate == "ALLOW"
    assert envelope.reason_code == "GUARD_ALLOW"


def test_real_guard_produces_hold_for_too_many_unknowns():
    envelope = decide_with_real_current_main_guard(
        payload("bank", unknowns=("u1", "u2")),
        source_root=UPSTREAM,
        confidence=0.90,
    )
    assert envelope.x108_gate == "HOLD"
    assert envelope.reason_code == "UNKNOWNS_OR_CONFIDENCE_LOW"


def test_real_guard_produces_block_for_contradiction_threshold():
    envelope = decide_with_real_current_main_guard(
        payload("bank", contradictions=("c1", "c2")),
        source_root=UPSTREAM,
        confidence=0.90,
    )
    assert envelope.x108_gate == "BLOCK"
    assert envelope.reason_code == "CONTRADICTION_THRESHOLD_REACHED"


def test_provenance_is_conserved_as_upstream_evidence():
    aggregate = governance_payload_to_real_upstream_aggregate(
        payload("bank"),
        source_root=UPSTREAM,
        confidence=0.90,
    )
    assert "evidence:1" in aggregate.evidence_refs
    assert "provenance:upstream-main" in aggregate.evidence_refs
    assert aggregate.extra_metrics["universal_payload_can_decide"] is False
    assert aggregate.extra_metrics["universal_payload_can_act"] is False


def test_administration_is_rejected_before_real_guard():
    with pytest.raises(
        UnsupportedCurrentMainDomain,
        match="NO_CANONICAL_DOMAIN_PIPELINE:administration",
    ):
        decide_with_real_current_main_guard(
            payload("administration"),
            source_root=UPSTREAM,
            confidence=0.90,
        )


def test_current_main_gps_alias_is_bounded_to_canonical_gps_domain_if_present():
    domains = set(current_main_supported_domains(UPSTREAM))
    if "gps" not in domains:
        pytest.skip("current main has no gps alias")

    envelope = decide_with_real_current_main_guard(
        payload("gps"),
        source_root=UPSTREAM,
        confidence=0.90,
    )
    assert envelope.domain == "gps_defense_aviation"
