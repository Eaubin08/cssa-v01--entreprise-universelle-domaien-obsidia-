from dataclasses import replace

from organizations.cssa.intake.real_readonly_pilot_preflight_v0 import (
    STATUS_AUTH_MISSING,
    STATUS_BLOCKED,
    STATUS_NO_CLUB_SOURCE,
    STATUS_REGISTRATION_MISSING,
    STATUS_VALIDATED,
    assess_cssa_real_readonly_pilot_v0,
)
from organizations.cssa.intake.real_source_onboarding_v0 import (
    build_human_operational_source_authorization_v0,
    build_observed_source_candidate_v0,
    activate_operational_source_v0,
)
from organizations.cssa.intake.operational_source_registry_v0 import (
    OperationalSourceRegistryV0,
)

T0 = "2026-10-08T08:00:00+00:00"

def source():
    return build_observed_source_candidate_v0(
        candidate_id="synthetic-cssa-club-mailbox",
        source_kind="MAILBOX",
        provider="FIXTURE_MAIL",
        source_identity_sha256="a" * 64,
        observed_capabilities=("LIST", "READ_MESSAGE", "SEND"),
        connector_reference="fixture-club-mailbox",
        observed_at=T0,
    )

def authorize(candidate, caps=("READ_MESSAGE",)):
    return build_human_operational_source_authorization_v0(
        candidate=candidate,
        authorization_id="synthetic-human-auth",
        approved_capabilities=caps,
        authority_reference="HUMAN_FIXTURE_ONLY",
        approved_by="HUMAN:FIXTURE_OPERATOR",
        authorized_at=T0,
    )

def test_actual_context_has_no_club_operational_source():
    result = assess_cssa_real_readonly_pilot_v0()
    assert result["verdict"] == STATUS_NO_CLUB_SOURCE
    assert result["pilot_started"] is False
    assert result["allows_club_operational_ingestion"] is False
    assert result["source_content_read"] is False
    assert result["decision_authority"] == "KX108_ONLY"

def test_personal_gmail_cannot_become_cssa_operational_source():
    result = assess_cssa_real_readonly_pilot_v0(
        source_scope="PERSONAL_INBOX", candidate=source(),
        authorization=authorize(source()),
    )
    assert result["verdict"] == STATUS_NO_CLUB_SOURCE
    assert result["checks"]["club_owned_source_scope_claimed"] is False
    assert result["allows_club_operational_ingestion"] is False

def test_observed_candidate_alone_is_not_sufficient():
    result = assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL", candidate=source(),
    )
    assert result["verdict"] == STATUS_AUTH_MISSING
    assert result["checks"]["source_observed_and_verified"] is True
    assert result["checks"]["human_authorization_exact_verified"] is False

def test_exact_human_auth_still_requires_registry_activation():
    c=source()
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,authorization=authorize(c),
    )
    assert result["verdict"] == STATUS_REGISTRATION_MISSING
    assert result["checks"]["readonly_capabilities_only"] is True

def test_write_capability_refused_despite_connector_offering_it():
    c=source()
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,
        authorization=authorize(c,("SEND",)),
    )
    assert result["verdict"] == STATUS_BLOCKED
    assert result["reasons"] == ["READONLY_CAPABILITY_SUBSET_REQUIRED"]

def test_candidate_or_human_authorization_tamper_fails_closed():
    c=source()
    tampered_c=replace(c,provider="ALTERED")
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=tampered_c,
    )
    assert result["verdict"] == STATUS_BLOCKED
    assert "HASH_MISMATCH" in result["reasons"][0]
    altered_auth=replace(authorize(c),candidate_hash="1"*64)
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,
        authorization=altered_auth,
    )
    assert result["verdict"] == STATUS_BLOCKED

def test_real_f3h_g_registry_chain_accepts_exact_synthetic_registration(tmp_path):
    c=source()
    a=authorize(c)
    registry=OperationalSourceRegistryV0(tmp_path/"registry")
    registration,receipt=activate_operational_source_v0(
        candidate=c,authorization=a,registry=registry,
        source_id="synthetic-cssa-mailbox",activated_at=T0,
    )
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,authorization=a,
        registration=registration,registry=registry,
    )
    assert result["verdict"] == STATUS_VALIDATED
    assert all(result["checks"].values())
    assert result["pilot_started"] is False
    assert result["source_connection_performed"] is False
    assert result["source_registration_performed"] is False
    assert result["allows_club_operational_ingestion"] is False
    assert result["human_operator_permission_still_required"] is True
    assert receipt.readonly is True

def test_cross_source_identity_and_registration_drift_fail_closed(tmp_path):
    c=source()
    a=authorize(c)
    registry=OperationalSourceRegistryV0(tmp_path/"registry")
    registration,_=activate_operational_source_v0(
        candidate=c,authorization=a,registry=registry,
        source_id="synthetic-cssa-mailbox",activated_at=T0,
    )
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,
        authorization=a,registration=replace(registration,source_identity_sha256="b"*64),
        registry=registry,
    )
    assert result["verdict"] == STATUS_BLOCKED

def test_registration_must_be_current_and_active(tmp_path):
    c=source();a=authorize(c)
    registry=OperationalSourceRegistryV0(tmp_path/"registry")
    registration,_=activate_operational_source_v0(
        candidate=c,authorization=a,registry=registry,
        source_id="synthetic-cssa-mailbox",activated_at=T0,
    )
    other=OperationalSourceRegistryV0(tmp_path/"another-registry")
    result=assess_cssa_real_readonly_pilot_v0(
        source_scope="CSSA_INTERNAL",candidate=c,
        authorization=a,registration=registration,registry=other,
    )
    assert result["verdict"] == STATUS_BLOCKED
    assert result["reasons"] == ["REGISTERED_SOURCE_MISSING_OR_REVOKED"]
