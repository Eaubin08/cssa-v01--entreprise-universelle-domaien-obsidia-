"""F3H-H CSSA real READONLY pilot preflight.

This is an inspection-only gate around existing F3H-G/F3H-F contracts.
It does not connect, poll, read mail, authorize operators or activate
a source. It cannot substitute for the club's actual permission.
"""
from __future__ import annotations

from typing import Any

from organizations.cssa.intake.real_source_onboarding_v0 import (
    HumanOperationalSourceAuthorizationV0,
    ObservedSourceCandidateV0,
    verify_human_operational_source_authorization_v0,
    verify_observed_source_candidate_v0,
)
from organizations.cssa.intake.operational_source_registry_v0 import (
    DECISION_AUTHORITY,
    READONLY_CAPABILITIES,
    OperationalSourceRegistrationV0,
    OperationalSourceRegistryV0,
    verify_operational_source_registration_v0,
)

STATUS_NO_CLUB_SOURCE = "PENDING_REAL_CSSA_OPERATIONAL_SOURCE"
STATUS_AUTH_MISSING = "PENDING_EXACT_HUMAN_AUTHORIZATION"
STATUS_REGISTRATION_MISSING = "PENDING_READONLY_REGISTRATION"
STATUS_VALIDATED = "PRECHECK_READONLY_SOURCE_REGISTERED_NOT_INGESTING"
STATUS_BLOCKED = "BLOCKED_PRECHECK"

def assess_cssa_real_readonly_pilot_v0(
    *,
    source_scope: str = "UNVERIFIED",
    candidate: ObservedSourceCandidateV0 | None = None,
    authorization: HumanOperationalSourceAuthorizationV0 | None = None,
    registration: OperationalSourceRegistrationV0 | None = None,
    registry: OperationalSourceRegistryV0 | None = None,
) -> dict[str, Any]:
    """Return readiness only; never load provider content or mutate a registry."""
    verdict = STATUS_NO_CLUB_SOURCE
    reasons: list[str] = []
    checks: dict[str, bool] = {
        "club_owned_source_scope_claimed": source_scope == "CSSA_INTERNAL",
        "source_observed_and_verified": False,
        "human_authorization_exact_verified": False,
        "readonly_capabilities_only": False,
        "registration_exact_verified": False,
        "registered_source_active": False,
    }

    if source_scope != "CSSA_INTERNAL":
        reasons.append("NOT_AN_ATTESTED_INTERNAL_CSSA_SOURCE")
    elif candidate is None:
        reasons.append("OBSERVED_INTERNAL_SOURCE_CANDIDATE_MISSING")
    else:
        ok, reason = verify_observed_source_candidate_v0(candidate)
        if not ok:
            verdict = STATUS_BLOCKED
            reasons.append(str(reason))
        else:
            checks["source_observed_and_verified"] = True
            if authorization is None:
                verdict = STATUS_AUTH_MISSING
                reasons.append("EXACT_HUMAN_AUTHORIZATION_MISSING")
            else:
                ok, reason = verify_human_operational_source_authorization_v0(
                    authorization, candidate=candidate
                )
                if not ok:
                    verdict = STATUS_BLOCKED
                    reasons.append(str(reason))
                elif not authorization.approved_capabilities or not set(
                    authorization.approved_capabilities
                ).issubset(READONLY_CAPABILITIES):
                    verdict = STATUS_BLOCKED
                    reasons.append("READONLY_CAPABILITY_SUBSET_REQUIRED")
                else:
                    checks["human_authorization_exact_verified"] = True
                    checks["readonly_capabilities_only"] = True
                    if registration is None or registry is None:
                        verdict = STATUS_REGISTRATION_MISSING
                        reasons.append("F3H_F_ACTIVE_REGISTRATION_REQUIRED")
                    else:
                        ok, reason = verify_operational_source_registration_v0(
                            registration
                        )
                        if not ok:
                            verdict = STATUS_BLOCKED
                            reasons.append(str(reason))
                        elif (
                            registration.source_kind != candidate.source_kind
                            or registration.provider != candidate.provider
                            or registration.source_identity_sha256
                            != candidate.source_identity_sha256
                            or tuple(registration.capabilities)
                            != tuple(authorization.approved_capabilities)
                            or registration.authority_reference != (
                                "onboarding-authorization:"
                                + authorization.authorization_hash
                            )
                        ):
                            verdict = STATUS_BLOCKED
                            reasons.append("REGISTRATION_ONBOARDING_BINDING_MISMATCH")
                        else:
                            checks["registration_exact_verified"] = True
                            registered = registry.load(registration.source_id)
                            if (
                                registered is None
                                or registered.registration_hash != registration.registration_hash
                                or not registry.is_active(registration.source_id)
                            ):
                                verdict = STATUS_BLOCKED
                                reasons.append("REGISTERED_SOURCE_MISSING_OR_REVOKED")
                            else:
                                checks["registered_source_active"] = True
                                verdict = STATUS_VALIDATED

    return {
        "schema": "CSSA_REAL_READONLY_PILOT_PREFLIGHT_V0",
        "verdict": verdict,
        "checks": checks,
        "reasons": reasons,
        "pilot_started": False,
        "source_content_read": False,
        "external_mutation_allowed": False,
        "source_connection_performed": False,
        "source_registration_performed": False,
        "raw_source_identity_persisted": False,
        "credentials_persisted": False,
        "allows_club_operational_ingestion": False,
        "human_operator_permission_still_required": True,
        "allowed_to_decide": False,
        "allowed_to_act": False,
        "decision_authority": DECISION_AUTHORITY,
    }
