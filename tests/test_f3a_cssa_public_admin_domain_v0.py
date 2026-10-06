import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.public_admin_v0 import (
    AUTHORITY_LGEF_COMPETITIONS,
    CASE_FIXTURE_CHANGE,
    CHANNEL_FOOTCLUBS,
    CHANNEL_OFFICIAL_EMAIL,
    CHANNEL_PAPER_FALLBACK,
    assess_club_info_update,
    assess_fixture_change,
    assess_fmi,
    assess_official_correspondence,
    cssa_public_case_adapter,
)
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import ActionCandidate  # noqa: E402
from scripts.providers.canonical_runtime_receipt_flow_v1 import (  # noqa: E402
    CanonicalRuntimeReceiptFlow,
)
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402


VALID_AT = "2026-10-06T20:00:00Z"
AGENT_ID = "DATA_PURITY_AGENT"


def test_fixture_change_normal_window_uses_footclubs_and_external_homologation():
    out = assess_fixture_change(
        case_ref="fixture:cssa:1",
        valid_at=VALID_AT,
        days_before_match=12,
        via_footclubs=True,
        official_email_agreement=False,
        homologated_by_lgef=True,
    )
    assert out.case_type == CASE_FIXTURE_CHANGE
    assert out.required_channel == CHANNEL_FOOTCLUBS
    assert out.final_authority == AUTHORITY_LGEF_COMPETITIONS
    assert out.status_candidate == "NORMAL_WINDOW"
    assert out.unknowns == ()
    assert out.risk_flags == ()
    assert out.allowed_to_decide is False
    assert out.allowed_to_act is False


def test_fixture_change_late_window_requires_official_email_and_cannot_self_homologate():
    out = assess_fixture_change(
        case_ref="fixture:cssa:2",
        valid_at=VALID_AT,
        days_before_match=5,
        via_footclubs=False,
        official_email_agreement=False,
        homologated_by_lgef=None,
    )
    assert out.required_channel == CHANNEL_OFFICIAL_EMAIL
    assert out.final_authority == AUTHORITY_LGEF_COMPETITIONS
    assert "LATE_CHANGE_CLUB_AGREEMENT_MISSING" in out.risk_flags
    assert "LGEF_HOMOLOGATION_UNKNOWN" in out.unknowns
    assert out.human_validation_required is True


def test_fmi_normal_path_detects_missed_public_deadline():
    out = assess_fmi(
        case_ref="match:cssa:home:1",
        valid_at=VALID_AT,
        cssa_is_receiving_club=True,
        fmi_available=True,
        transmitted_by_next_day_10=False,
    )
    assert out.required_channel == "FMI"
    assert "FMI_TRANSMISSION_DEADLINE_MISSED" in out.risk_flags


def test_fmi_exception_uses_paper_fallback_and_preserves_commission_review():
    out = assess_fmi(
        case_ref="match:cssa:home:2",
        valid_at=VALID_AT,
        cssa_is_receiving_club=True,
        fmi_available=False,
        transmitted_by_next_day_10=None,
        paper_fallback_sent_in_time=True,
    )
    assert out.required_channel == CHANNEL_PAPER_FALLBACK
    assert out.status_candidate == "FMI_EXCEPTION_PAPER_FALLBACK"
    assert "FMI_TECHNICAL_EXCEPTION_REQUIRES_COMMISSION_REVIEW" in out.risk_flags
    assert out.allowed_to_act is False


def test_official_correspondence_flags_non_official_sender():
    out = assess_official_correspondence(
        case_ref="mail:1",
        valid_at=VALID_AT,
        outbound_to_lgef_or_district=True,
        sent_from_official_club_address=False,
    )
    assert out.required_channel == CHANNEL_OFFICIAL_EMAIL
    assert "NON_OFFICIAL_SENDER_ADDRESS" in out.risk_flags


def test_club_information_change_after_10_days_is_flagged():
    out = assess_club_info_update(
        case_ref="club-info:1",
        valid_at=VALID_AT,
        days_since_change=11,
        notified_lgef=False,
    )
    assert "CLUB_INFORMATION_UPDATE_DEADLINE_MISSED" in out.risk_flags


def test_cssa_public_case_maps_to_generic_administration_without_business_leak():
    out = assess_fixture_change(
        case_ref="fixture:cssa:3",
        valid_at=VALID_AT,
        days_before_match=12,
        via_footclubs=True,
        official_email_agreement=False,
        homologated_by_lgef=True,
    )
    raw = out.to_runtime_mapping(confidence=0.92)
    state = cssa_public_case_adapter(raw)

    assert state.domain_id == "administration"
    assert state.state_ref == "cssa:fixture_change:fixture:cssa:3"
    assert state.decision_authority == "KX108_ONLY"
    assert state.allowed_to_decide is False
    assert state.allowed_to_act is False

    # CSSA business fields exist locally but stop at the adapter boundary.
    assert "required_channel" in raw
    assert not hasattr(state, "required_channel")
    assert not hasattr(state, "final_authority")


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.public.admin.v0",
            schema_ref="organizations/cssa/public_admin_v0.py",
            capabilities=("read", "classify", "link", "propose"),
        ),
        cssa_public_case_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.public.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


class CountingProvider:
    def __init__(self):
        self.invocations = 0

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": "cssa-public-readonly-provider",
            "provider": "cssa_public_readonly",
        }


def test_real_cssa_public_fixture_case_crosses_first_class_runtime_readonly(tmp_path):
    assessment = assess_fixture_change(
        case_ref="fixture:cssa:runtime:1",
        valid_at=VALID_AT,
        days_before_match=12,
        via_footclubs=True,
        official_email_agreement=False,
        homologated_by_lgef=True,
    )
    raw = assessment.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_public_readonly", provider)

    action = ActionCandidate(
        action_id="cssa-public-fixture-classify",
        domain="administration",
        actor_id="f3a",
        intent="classify_public_fixture_change",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": 2,
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id="mission-cssa-public-fixture",
        provider_id="cssa_public_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_PUBLIC_CLASSIFICATION",
            "case_ref": assessment.case_ref,
        },
        agent_context_store_dir=tmp_path / "contexts",
        decision_store_dir=tmp_path / "decisions",
        domain_extension_resolver=make_resolver(),
    )

    assert result.domain == "administration"
    assert result.x108_gate == "ALLOW"
    assert result.decision_record_verified is True
    assert result.replay_status == "PASS"
    assert result.execution_authorized is True
    assert result.provider_invoked is True
    assert provider.invocations == 1
    assert result.receipt["status"] == "COMPLETED"

    # Still only bounded internal analysis.
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False
    assert result.decision_authority == "KX108_ONLY"
