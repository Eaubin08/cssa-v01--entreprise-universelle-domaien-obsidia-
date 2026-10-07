import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REAL_EVIDENCE = (
    ROOT
    / "evidence"
    / "pilots"
    / "F3H_E_REAL_READONLY_GMAIL_CALIBRATION_V0.json"
)

from organizations.cssa.intake.readonly_router_v0 import (
    CLASS_ACCOUNTING_DOCUMENT,
    CLASS_DEADLINE_OBLIGATION,
    CLASS_INCIDENT_ALERT,
    CLASS_MARKETING_COMMUNICATION,
    CLASS_MATCHDAY_INFORMATION,
    CLASS_NON_CSSA,
    CLASS_OPERATIONAL_ACTION_REQUEST,
    CLASS_TICKETING_TRANSACTION,
    CLASS_UNKNOWN_CSSA,
    ROUTE_IGNORE,
    ROUTE_NATIVE_CASE_TASK,
    ROUTE_NATIVE_CASE_TASK_CALENDAR,
    ROUTE_PERSONAL_TRANSACTION,
    ROUTE_REVIEW_HOLD,
    ROUTE_SHADOW_INTERACTION,
    SOURCE_CSSA_OPERATIONAL_MAILBOX,
    SOURCE_PERSONAL_INBOX,
    build_native_intake_candidate_from_route_v0,
    build_readonly_message_observation_v0,
    route_readonly_observation_v0,
    verify_readonly_message_observation_v0,
    verify_readonly_route_decision_v0,
)
from organizations.cssa.native_ops.cssa_native_ops_bridge_v0 import (
    execute_cssa_native_intake_v0,
)


def observe(
    *,
    message_id: str,
    subject: str,
    body: str,
    source_scope: str,
    has_attachment: bool = False,
):
    return build_readonly_message_observation_v0(
        provider_message_id=message_id,
        subject=subject,
        body=body,
        sender_family="TEST_SOURCE",
        received_at="2026-10-07T10:00:00+00:00",
        source_scope=source_scope,
        has_attachment=has_attachment,
    )


def test_real_gmail_calibration_is_privacy_minimized_and_never_internal_truth():
    data = json.loads(REAL_EVIDENCE.read_text(encoding="utf-8"))

    assert data["status"] == "REAL_PROVIDER_READONLY_OBSERVED_PRIVACY_MINIMIZED"
    assert data["source_scope"] == "PERSONAL_INBOX"
    assert data["real_internal_cssa_evidence"] is False
    assert data["raw_provider_message_id_persisted"] is False
    assert data["raw_subject_persisted"] is False
    assert data["raw_body_persisted"] is False
    assert data["raw_recipient_persisted"] is False
    assert len(data["samples"]) == 8

    allowed_routes = {
        ROUTE_SHADOW_INTERACTION,
        ROUTE_PERSONAL_TRANSACTION,
    }
    for sample in data["samples"]:
        assert len(sample["provider_message_id_sha256"]) == 64
        assert len(sample["subject_sha256"]) == 64
        assert sample["route"] in allowed_routes
        assert "subject" not in sample
        assert "body" not in sample
        assert "provider_message_id" not in sample

    assert data["search_findings"]["operational_cssa_sender_messages_found"] is False
    assert data["search_findings"]["direct_action_required_cssa_messages_found"] is False


@pytest.mark.parametrize(
    "subject,body,expected_class,expected_route",
    [
        (
            "Rendez-vous samedi à Dugauguez",
            (
                "CS Sedan Ardennes au Stade Louis-Dugauguez. "
                "Ouverture des portes 17h30. Coup d'envoi 18h30. "
                "Buvette et billetterie ouvertes."
            ),
            CLASS_MATCHDAY_INFORMATION,
            ROUTE_SHADOW_INTERACTION,
        ),
        (
            "Le nouveau maillot Third du CSSA est disponible",
            (
                "CS Sedan Ardennes. Nouveau maillot disponible sur "
                "la boutique officielle. Découvrir le maillot."
            ),
            CLASS_MARKETING_COMMUNICATION,
            ROUTE_SHADOW_INTERACTION,
        ),
        (
            "Votre commande pour CS Sedan",
            (
                "Merci pour votre commande ! CS Sedan. "
                "Votre commande est confirmée. Télécharger ma facture."
            ),
            CLASS_TICKETING_TRANSACTION,
            ROUTE_PERSONAL_TRANSACTION,
        ),
        (
            "Votre Facture pour CS SEDAN ARDENNES",
            (
                "Votre Facture CS SEDAN ARDENNES. "
                "Ce document est une pièce comptable. Service facturation."
            ),
            CLASS_ACCOUNTING_DOCUMENT,
            ROUTE_PERSONAL_TRANSACTION,
        ),
    ],
)
def test_personal_mail_classes_do_not_create_native_work(
    subject,
    body,
    expected_class,
    expected_route,
):
    observation = observe(
        message_id=f"personal:{expected_class}",
        subject=subject,
        body=body,
        source_scope=SOURCE_PERSONAL_INBOX,
    )
    assert verify_readonly_message_observation_v0(observation) == (True, None)

    route = route_readonly_observation_v0(observation)
    assert route.classification == expected_class
    assert route.route == expected_route
    assert route.canonical_native_candidate is False
    assert route.real_internal_cssa_evidence is False
    assert verify_readonly_route_decision_v0(
        observation,
        route,
    ) == (True, None)


def test_action_request_from_personal_inbox_holds_not_promotes():
    observation = observe(
        message_id="personal-action",
        subject="CSSA - action requise",
        body=(
            "CS Sedan Ardennes. Merci de nous transmettre le dossier. "
            "Réponse attendue."
        ),
        source_scope=SOURCE_PERSONAL_INBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_OPERATIONAL_ACTION_REQUEST
    assert route.route == ROUTE_REVIEW_HOLD
    assert route.canonical_native_candidate is False
    assert route.requires_human_review is True


def test_trusted_operational_action_routes_to_native_case_task():
    observation = observe(
        message_id="operational-action",
        subject="CSSA - action requise",
        body=(
            "CS Sedan Ardennes. Merci de nous transmettre le dossier. "
            "Réponse attendue."
        ),
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_OPERATIONAL_ACTION_REQUEST
    assert route.route == ROUTE_NATIVE_CASE_TASK
    assert route.canonical_native_candidate is True
    assert route.calendar_candidate is False
    assert route.real_internal_cssa_evidence is True


def test_trusted_operational_deadline_routes_to_calendar_candidate():
    observation = observe(
        message_id="operational-deadline",
        subject="CSSA - dossier à transmettre",
        body=(
            "CS Sedan Ardennes. Merci de nous transmettre le dossier "
            "avant le 10 octobre. Réponse attendue."
        ),
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_DEADLINE_OBLIGATION
    assert route.route == ROUTE_NATIVE_CASE_TASK_CALENDAR
    assert route.canonical_native_candidate is True
    assert route.calendar_candidate is True


def test_trusted_operational_incident_routes_to_case_task():
    observation = observe(
        message_id="operational-incident",
        subject="CSSA - incident opérationnel",
        body=(
            "CS Sedan Ardennes. Incident détecté sur le contrôle d'accès. "
            "Blocage confirmé."
        ),
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_INCIDENT_ALERT
    assert route.route == ROUTE_NATIVE_CASE_TASK
    assert route.canonical_native_candidate is True


def test_unknown_cssa_semantics_hold_for_review():
    observation = observe(
        message_id="unknown-cssa",
        subject="CSSA information",
        body="CS Sedan Ardennes. Message sans sémantique opérationnelle prouvée.",
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_UNKNOWN_CSSA
    assert route.route == ROUTE_REVIEW_HOLD
    assert route.canonical_native_candidate is False


def test_non_cssa_mail_is_ignored():
    observation = observe(
        message_id="other-mail",
        subject="Autre sujet",
        body="Message totalement extérieur au club.",
        source_scope=SOURCE_PERSONAL_INBOX,
    )
    route = route_readonly_observation_v0(observation)
    assert route.classification == CLASS_NON_CSSA
    assert route.route == ROUTE_IGNORE
    assert route.canonical_native_candidate is False


def test_route_tamper_cannot_create_native_candidate():
    observation = observe(
        message_id="tamper-action",
        subject="CSSA - action requise",
        body="CS Sedan Ardennes. Merci de nous répondre.",
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    object.__setattr__(route, "calendar_candidate", True)

    ok, reason = verify_readonly_route_decision_v0(observation, route)
    assert ok is False
    assert reason == "READONLY_ROUTE_RECOMPUTE_MISMATCH"

    with pytest.raises(
        ValueError,
        match="READONLY_ROUTE_RECOMPUTE_MISMATCH",
    ):
        build_native_intake_candidate_from_route_v0(
            observation=observation,
            route=route,
            cssa_case_id="tamper-case",
            case_type="ADMIN_ACTION",
            title="Tamper",
            summary="Tamper",
            owner_ref="role:manager_general",
            priority="NORMAL",
            due_at="2026-10-08T12:00:00+00:00",
            source_refs=("fixture:tamper",),
            evidence_refs=("fixture:tamper",),
        )


def test_operational_deadline_can_feed_f3h_d_native_bridge_end_to_end(tmp_path):
    observation = observe(
        message_id="operational-deadline-e2e",
        subject="CSSA - dossier à transmettre",
        body=(
            "CS Sedan Ardennes. Merci de nous transmettre le dossier "
            "avant le 10 octobre. Réponse attendue."
        ),
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)
    plan = build_native_intake_candidate_from_route_v0(
        observation=observation,
        route=route,
        cssa_case_id="operational-deadline-e2e",
        case_type="DEADLINE_OBLIGATION",
        title="Dossier à transmettre",
        summary="Demande opérationnelle simulée avec échéance explicite.",
        owner_ref="role:manager_general",
        priority="HIGH",
        due_at="2026-10-10T17:00:00+00:00",
        source_refs=("fixture:operational-mailbox",),
        evidence_refs=("fixture:synthetic-action-request",),
        tags=("READONLY_ROUTER",),
    )

    result = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference="fixture:f3h-e-e2e",
    )
    assert result["status"] == "CSSA_NATIVE_INTAKE_COMMITTED"
    assert result["canonical_mutation_count"] == 4
    assert result["external_action"] is False
    assert result["external_saas_required"] is False


def test_native_candidate_requires_resolved_due_at():
    observation = observe(
        message_id="action-no-due",
        subject="CSSA - action requise",
        body="CS Sedan Ardennes. Merci de nous transmettre le dossier.",
        source_scope=SOURCE_CSSA_OPERATIONAL_MAILBOX,
    )
    route = route_readonly_observation_v0(observation)

    with pytest.raises(
        ValueError,
        match="READONLY_NATIVE_CANDIDATE_DUE_AT_REQUIRED",
    ):
        build_native_intake_candidate_from_route_v0(
            observation=observation,
            route=route,
            cssa_case_id="action-no-due",
            case_type="ADMIN_ACTION",
            title="Action",
            summary="Action sans échéance résolue.",
            owner_ref="role:manager_general",
            priority="NORMAL",
            due_at=None,
            source_refs=("fixture:source",),
            evidence_refs=("fixture:evidence",),
        )
