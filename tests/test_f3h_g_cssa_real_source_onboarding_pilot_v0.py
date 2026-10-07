from pathlib import Path

import pytest

from organizations.cssa.intake.operational_source_registry_v0 import (
    OperationalSourceRegistryV0,
    SOURCE_DOCUMENT_REPOSITORY,
    SOURCE_MAILBOX,
)
from organizations.cssa.intake.real_source_onboarding_v0 import (
    activate_operational_source_v0,
    build_human_operational_source_authorization_v0,
    build_observed_source_candidate_v0,
    verify_human_operational_source_authorization_v0,
    verify_observed_source_candidate_v0,
    verify_operational_source_activation_receipt_v0,
)

T0 = "2026-10-07T12:00:00+00:00"
T1 = "2026-10-07T12:05:00+00:00"


def mailbox_candidate():
    return build_observed_source_candidate_v0(
        candidate_id="candidate:cssa-mailbox",
        source_kind=SOURCE_MAILBOX,
        provider="GMAIL",
        source_identity_sha256="a" * 64,
        observed_capabilities=("SEARCH", "READ_MESSAGE", "READ_ATTACHMENT"),
        connector_reference="connector:gmail:observed",
        observed_at=T0,
    )


def document_candidate():
    return build_observed_source_candidate_v0(
        candidate_id="candidate:cssa-docs",
        source_kind=SOURCE_DOCUMENT_REPOSITORY,
        provider="GOOGLE_DRIVE",
        source_identity_sha256="b" * 64,
        observed_capabilities=("SEARCH", "READ_DOCUMENT", "READ_FILE_METADATA"),
        connector_reference="connector:drive:observed",
        observed_at=T0,
    )


def authorize(candidate, capabilities=None):
    return build_human_operational_source_authorization_v0(
        candidate=candidate,
        authorization_id=f"auth:{candidate.candidate_id}",
        approved_capabilities=capabilities or candidate.observed_capabilities,
        authority_reference=f"human-review:{candidate.candidate_id}",
        approved_by="HUMAN:CSSA_OPERATOR",
        authorized_at=T1,
    )


def test_observed_candidate_is_non_sovereign_and_not_self_claimed():
    candidate = mailbox_candidate()
    assert verify_observed_source_candidate_v0(candidate) == (True, None)
    assert candidate.internal_cssa_source_claimed is False
    assert candidate.allowed_to_decide is False
    assert candidate.allowed_to_act is False
    assert candidate.raw_source_identity_persisted is False
    assert candidate.raw_credentials_persisted is False
    assert candidate.decision_authority == "KX108_ONLY"


def test_human_authorization_binds_exact_candidate_and_capabilities():
    candidate = mailbox_candidate()
    authorization = authorize(
        candidate,
        ("SEARCH", "READ_MESSAGE"),
    )
    assert verify_human_operational_source_authorization_v0(
        authorization,
        candidate=candidate,
    ) == (True, None)
    assert authorization.internal_cssa_source is True
    assert authorization.readonly_only is True
    assert authorization.is_execution_authority is False
    assert authorization.approved_capabilities == (
        "READ_MESSAGE",
        "SEARCH",
    )


def test_machine_cannot_authorize_source():
    candidate = mailbox_candidate()
    with pytest.raises(
        ValueError,
        match="SOURCE_ONBOARDING_HUMAN_AUTHORIZATION_REQUIRED",
    ):
        build_human_operational_source_authorization_v0(
            candidate=candidate,
            authorization_id="auth:machine",
            approved_capabilities=("READ_MESSAGE",),
            authority_reference="fixture:machine",
            approved_by="MACHINE",
            authorized_at=T1,
        )


def test_capability_escalation_beyond_observed_connector_is_forbidden():
    candidate = mailbox_candidate()
    with pytest.raises(
        ValueError,
        match="SOURCE_ONBOARDING_CAPABILITY_ESCALATION_FORBIDDEN",
    ):
        authorize(candidate, ("READ_MESSAGE", "READ_THREAD"))


def test_changed_source_identity_invalidates_prior_authorization():
    candidate = mailbox_candidate()
    authorization = authorize(candidate)

    changed = build_observed_source_candidate_v0(
        candidate_id=candidate.candidate_id,
        source_kind=candidate.source_kind,
        provider=candidate.provider,
        source_identity_sha256="c" * 64,
        observed_capabilities=candidate.observed_capabilities,
        connector_reference=candidate.connector_reference,
        observed_at=candidate.observed_at,
    )
    ok, reason = verify_human_operational_source_authorization_v0(
        authorization,
        candidate=changed,
    )
    assert ok is False
    assert reason == "SOURCE_ONBOARDING_AUTHORIZATION_CANDIDATE_HASH_MISMATCH"


def test_changed_observed_capabilities_invalidate_prior_authorization():
    candidate = mailbox_candidate()
    authorization = authorize(candidate)

    changed = build_observed_source_candidate_v0(
        candidate_id=candidate.candidate_id,
        source_kind=candidate.source_kind,
        provider=candidate.provider,
        source_identity_sha256=candidate.source_identity_sha256,
        observed_capabilities=("SEARCH", "READ_MESSAGE"),
        connector_reference=candidate.connector_reference,
        observed_at=candidate.observed_at,
    )
    ok, reason = verify_human_operational_source_authorization_v0(
        authorization,
        candidate=changed,
    )
    assert ok is False
    assert reason == "SOURCE_ONBOARDING_AUTHORIZATION_CANDIDATE_HASH_MISMATCH"


def test_mailbox_activation_registers_readonly_and_prepares_f3h_e_authority(
    tmp_path,
):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    candidate = mailbox_candidate()
    authorization = authorize(candidate, ("SEARCH", "READ_MESSAGE"))

    registration, receipt = activate_operational_source_v0(
        candidate=candidate,
        authorization=authorization,
        registry=registry,
        source_id="cssa-mailbox-real-pilot",
        activated_at=T1,
    )

    assert registry.is_active(registration.source_id) is True
    assert registration.source_kind == SOURCE_MAILBOX
    assert registration.capabilities == ("READ_MESSAGE", "SEARCH")
    assert registration.readonly is True
    assert registration.external_mutation_allowed is False
    assert registration.is_execution_authority is False

    assert receipt.active is True
    assert receipt.readonly is True
    assert receipt.external_mutation_allowed is False
    assert receipt.f3h_e_mailbox_authority_ready is True
    assert verify_operational_source_activation_receipt_v0(
        receipt,
        candidate=candidate,
        authorization=authorization,
        registration=registration,
    ) == (True, None)


def test_document_repository_activation_registers_without_mailbox_authority(
    tmp_path,
):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    candidate = document_candidate()
    authorization = authorize(candidate)

    registration, receipt = activate_operational_source_v0(
        candidate=candidate,
        authorization=authorization,
        registry=registry,
        source_id="cssa-documents-real-pilot",
        activated_at=T1,
    )

    assert registration.source_kind == SOURCE_DOCUMENT_REPOSITORY
    assert registration.readonly is True
    assert registration.external_mutation_allowed is False
    assert receipt.f3h_e_mailbox_authority_ready is False
    assert verify_operational_source_activation_receipt_v0(
        receipt,
        candidate=candidate,
        authorization=authorization,
        registration=registration,
    ) == (True, None)


def test_authorization_tamper_is_detected():
    candidate = mailbox_candidate()
    authorization = authorize(candidate)
    data = authorization.to_dict()
    data["approved_by"] = "HUMAN:OTHER"
    ok, reason = verify_human_operational_source_authorization_v0(
        data,
        candidate=candidate,
    )
    assert ok is False
    assert reason == "SOURCE_ONBOARDING_AUTHORIZATION_HASH_MISMATCH"


def test_candidate_tamper_is_detected():
    candidate = mailbox_candidate()
    data = candidate.to_dict()
    data["provider"] = "OTHER"
    ok, reason = verify_observed_source_candidate_v0(data)
    assert ok is False
    assert reason == "SOURCE_ONBOARDING_CANDIDATE_HASH_MISMATCH"


def test_activation_receipt_tamper_is_detected(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    candidate = mailbox_candidate()
    authorization = authorize(candidate)
    registration, receipt = activate_operational_source_v0(
        candidate=candidate,
        authorization=authorization,
        registry=registry,
        source_id="cssa-mailbox-tamper",
        activated_at=T1,
    )
    data = receipt.to_dict()
    data["active"] = False
    ok, reason = verify_operational_source_activation_receipt_v0(
        data,
        candidate=candidate,
        authorization=authorization,
        registration=registration,
    )
    assert ok is False
    assert reason == "SOURCE_ONBOARDING_RECEIPT_HASH_MISMATCH"


def test_authorization_can_only_reduce_observed_capabilities():
    candidate = document_candidate()
    authorization = authorize(
        candidate,
        ("READ_DOCUMENT",),
    )
    assert authorization.approved_capabilities == ("READ_DOCUMENT",)
    assert set(authorization.approved_capabilities).issubset(
        set(candidate.observed_capabilities)
    )
