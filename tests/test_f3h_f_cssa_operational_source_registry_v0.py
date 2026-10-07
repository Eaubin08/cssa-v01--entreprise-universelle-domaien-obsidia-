import copy
from pathlib import Path

import pytest

from organizations.cssa.intake.operational_source_registry_v0 import (
    SOURCE_API_READONLY,
    SOURCE_CALENDAR,
    SOURCE_DOCUMENT_REPOSITORY,
    SOURCE_FORM_INBOX,
    SOURCE_MAILBOX,
    OperationalSourceRegistryV0,
    build_mailbox_observation_from_registered_source_v0,
    build_operational_source_registration_v0,
    build_readonly_source_item_v0,
    build_source_revocation_v0,
    mailbox_registration_to_f3h_e_authority_v0,
    verify_operational_source_registration_v0,
    verify_readonly_source_item_v0,
    verify_source_revocation_v0,
)
from organizations.cssa.intake.readonly_router_v0 import (
    CLASS_OPERATIONAL_ACTION_REQUEST,
    ROUTE_NATIVE_CASE_TASK,
    route_readonly_observation_v0,
)

T0 = "2026-10-07T11:00:00+00:00"
T1 = "2026-10-07T11:05:00+00:00"


def mailbox_registration():
    return build_operational_source_registration_v0(
        source_id="cssa-mailbox-primary",
        source_kind=SOURCE_MAILBOX,
        provider="GMAIL",
        source_identity_sha256="1" * 64,
        capabilities=("SEARCH", "READ_MESSAGE", "READ_ATTACHMENT"),
        authority_reference="human-approved:cssa-mailbox-primary",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )


def test_mailbox_registration_is_readonly_non_sovereign():
    registration = mailbox_registration()
    assert verify_operational_source_registration_v0(registration) == (
        True,
        None,
    )
    assert registration.readonly is True
    assert registration.external_mutation_allowed is False
    assert registration.is_execution_authority is False
    assert registration.decision_authority == "KX108_ONLY"
    assert registration.capabilities == (
        "READ_ATTACHMENT",
        "READ_MESSAGE",
        "SEARCH",
    )


@pytest.mark.parametrize(
    "capability",
    [
        "SEND",
        "SEND_EMAIL",
        "WRITE",
        "CREATE_DRAFT",
        "DELETE",
        "TRASH",
        "UPDATE_EVENT",
        "FORWARD",
        "UPLOAD",
        "EXECUTE",
    ],
)
def test_write_like_capabilities_are_forbidden(capability):
    with pytest.raises(
        ValueError,
        match="SOURCE_REGISTRY_WRITE_CAPABILITY_FORBIDDEN",
    ):
        build_operational_source_registration_v0(
            source_id=f"forbidden-{capability.lower().replace('_', '-')}",
            source_kind=SOURCE_MAILBOX,
            provider="GMAIL",
            source_identity_sha256="2" * 64,
            capabilities=("READ_MESSAGE", capability),
            authority_reference="fixture:forbidden",
            approved_by="HUMAN:CSSA_OPERATOR",
            registered_at=T0,
        )


def test_unknown_read_capability_is_rejected():
    with pytest.raises(
        ValueError,
        match="SOURCE_REGISTRY_CAPABILITY_UNSUPPORTED",
    ):
        build_operational_source_registration_v0(
            source_id="unknown-capability",
            source_kind=SOURCE_API_READONLY,
            provider="CUSTOM",
            source_identity_sha256="3" * 64,
            capabilities=("READ_EVERYTHING",),
            authority_reference="fixture:unknown",
            approved_by="HUMAN:CSSA_OPERATOR",
            registered_at=T0,
        )


def test_machine_cannot_register_operational_source():
    with pytest.raises(
        ValueError,
        match="SOURCE_REGISTRY_HUMAN_APPROVER_REQUIRED",
    ):
        build_operational_source_registration_v0(
            source_id="machine-source",
            source_kind=SOURCE_MAILBOX,
            provider="GMAIL",
            source_identity_sha256="4" * 64,
            capabilities=("READ_MESSAGE",),
            authority_reference="fixture:machine",
            approved_by="MACHINE",
            registered_at=T0,
        )


def test_registration_tamper_is_detected():
    registration = mailbox_registration()
    data = registration.to_dict()
    data["provider"] = "OTHER"
    ok, reason = verify_operational_source_registration_v0(data)
    assert ok is False
    assert reason == "SOURCE_REGISTRY_HASH_MISMATCH"


def test_registry_registration_is_immutable(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    original = mailbox_registration()
    registry.register(original)
    assert registry.load(original.source_id) == original
    assert registry.is_active(original.source_id) is True

    changed = build_operational_source_registration_v0(
        source_id=original.source_id,
        source_kind=SOURCE_MAILBOX,
        provider="GMAIL",
        source_identity_sha256="5" * 64,
        capabilities=("READ_MESSAGE",),
        authority_reference="changed",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )
    with pytest.raises(
        ValueError,
        match="SOURCE_REGISTRY_IMMUTABLE_REGISTRATION_CONFLICT",
    ):
        registry.register(changed)


def test_registered_mailbox_bridges_into_f3h_e_operational_route(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    registration = mailbox_registration()
    registry.register(registration)

    observation = build_mailbox_observation_from_registered_source_v0(
        registration=registration,
        registry=registry,
        provider_message_id="provider-message-001",
        subject="CSSA - action requise",
        body=(
            "CS Sedan Ardennes. Merci de nous transmettre le dossier. "
            "Réponse attendue."
        ),
        sender_family="CSSA_OPERATIONAL",
        received_at=T1,
        has_attachment=False,
    )
    assert observation.source_authority_hash is not None
    assert observation.raw_provider_message_id_persisted is False
    assert observation.raw_body_persisted is False
    assert observation.raw_recipient_persisted is False

    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_OPERATIONAL_ACTION_REQUEST
    assert route.route == ROUTE_NATIVE_CASE_TASK
    assert route.canonical_native_candidate is True
    assert route.real_internal_cssa_evidence is True


def test_revoked_mailbox_cannot_feed_f3h_e(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    registration = mailbox_registration()
    registry.register(registration)

    revocation = build_source_revocation_v0(
        registration=registration,
        revocation_id="revoke-mailbox-001",
        reason="Access removed",
        revoked_by="HUMAN:CSSA_OPERATOR",
        revoked_at=T1,
    )
    assert verify_source_revocation_v0(
        revocation,
        registration=registration,
    ) == (True, None)
    registry.revoke(revocation)
    assert registry.is_active(registration.source_id) is False

    with pytest.raises(
        ValueError,
        match="SOURCE_REGISTRY_SOURCE_REVOKED_OR_INACTIVE",
    ):
        build_mailbox_observation_from_registered_source_v0(
            registration=registration,
            registry=registry,
            provider_message_id="provider-message-002",
            subject="CSSA - action requise",
            body="CS Sedan Ardennes. Merci de nous répondre.",
            sender_family="CSSA_OPERATIONAL",
            received_at=T1,
            has_attachment=False,
        )


def test_non_mailbox_cannot_forge_mailbox_authority(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    registration = build_operational_source_registration_v0(
        source_id="cssa-drive",
        source_kind=SOURCE_DOCUMENT_REPOSITORY,
        provider="GOOGLE_DRIVE",
        source_identity_sha256="6" * 64,
        capabilities=("SEARCH", "READ_DOCUMENT", "READ_FILE_METADATA"),
        authority_reference="fixture:drive",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )
    registry.register(registration)

    with pytest.raises(ValueError, match="SOURCE_REGISTRY_NOT_MAILBOX"):
        mailbox_registration_to_f3h_e_authority_v0(
            registration=registration,
            registry=registry,
        )


@pytest.mark.parametrize(
    "source_kind,provider,capabilities",
    [
        (
            SOURCE_DOCUMENT_REPOSITORY,
            "GOOGLE_DRIVE",
            ("SEARCH", "READ_DOCUMENT", "READ_FILE_METADATA"),
        ),
        (
            SOURCE_CALENDAR,
            "GOOGLE_CALENDAR",
            ("SEARCH", "READ_EVENT"),
        ),
        (
            SOURCE_FORM_INBOX,
            "FORM_PROVIDER",
            ("LIST", "READ_FORM_RESPONSE"),
        ),
        (
            SOURCE_API_READONLY,
            "CUSTOM_API",
            ("LIST", "READ_API_RESOURCE"),
        ),
    ],
)
def test_generic_readonly_sources_register_without_execution_authority(
    tmp_path,
    source_kind,
    provider,
    capabilities,
):
    registry = OperationalSourceRegistryV0(tmp_path / source_kind)
    registration = build_operational_source_registration_v0(
        source_id=f"source-{source_kind.lower()}",
        source_kind=source_kind,
        provider=provider,
        source_identity_sha256="7" * 64,
        capabilities=capabilities,
        authority_reference=f"fixture:{source_kind}",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )
    registry.register(registration)
    assert registry.is_active(registration.source_id) is True
    assert registration.external_mutation_allowed is False
    assert registration.is_execution_authority is False


def test_readonly_document_item_is_privacy_minimized_and_bound_to_registry(
    tmp_path,
):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    registration = build_operational_source_registration_v0(
        source_id="cssa-docs",
        source_kind=SOURCE_DOCUMENT_REPOSITORY,
        provider="GOOGLE_DRIVE",
        source_identity_sha256="8" * 64,
        capabilities=("SEARCH", "READ_DOCUMENT", "READ_FILE_METADATA"),
        authority_reference="fixture:docs",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )
    registry.register(registration)

    item = build_readonly_source_item_v0(
        registration=registration,
        registry=registry,
        provider_item_id="raw-document-id",
        content="Internal fixture content.",
        metadata={"mime_type": "application/pdf", "title": "fixture"},
        observed_at=T1,
    )
    assert verify_readonly_source_item_v0(
        item,
        registration=registration,
    ) == (True, None)
    assert item.raw_provider_item_id_persisted is False
    assert item.raw_content_persisted is False
    assert item.raw_source_identity_persisted is False
    assert item.allowed_to_decide is False
    assert item.allowed_to_act is False
    assert item.decision_authority == "KX108_ONLY"


def test_readonly_source_item_tamper_is_detected(tmp_path):
    registry = OperationalSourceRegistryV0(tmp_path / "registry")
    registration = build_operational_source_registration_v0(
        source_id="cssa-api",
        source_kind=SOURCE_API_READONLY,
        provider="CUSTOM_API",
        source_identity_sha256="9" * 64,
        capabilities=("READ_API_RESOURCE",),
        authority_reference="fixture:api",
        approved_by="HUMAN:CSSA_OPERATOR",
        registered_at=T0,
    )
    registry.register(registration)
    item = build_readonly_source_item_v0(
        registration=registration,
        registry=registry,
        provider_item_id="resource-1",
        content="fixture",
        metadata={"kind": "record"},
        observed_at=T1,
    )
    data = item.to_dict()
    data["provider"] = "OTHER"
    ok, reason = verify_readonly_source_item_v0(
        data,
        registration=registration,
    )
    assert ok is False
    assert reason == "SOURCE_ITEM_PROVIDER_MISMATCH"


def test_revocation_tamper_is_detected():
    registration = mailbox_registration()
    revocation = build_source_revocation_v0(
        registration=registration,
        revocation_id="revocation-tamper",
        reason="Fixture",
        revoked_by="HUMAN:CSSA_OPERATOR",
        revoked_at=T1,
    )
    data = revocation.to_dict()
    data["reason"] = "tampered"
    ok, reason = verify_source_revocation_v0(
        data,
        registration=registration,
    )
    assert ok is False
    assert reason == "SOURCE_REGISTRY_REVOCATION_HASH_MISMATCH"
