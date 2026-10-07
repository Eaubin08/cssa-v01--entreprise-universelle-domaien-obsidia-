"""F3A — CSSA public-administration domain candidate.

This module models only facts derivable from public CSSA/FFF/LGEF sources.
It is NOT the CSSA internal operating model.

The output remains non-sovereign and maps into the already-tested
Administration universal contract. No external action is authorized here.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

from universal.contracts.domain_v0 import DomainStateRefV0


DOMAIN_ID = "administration"
ORGANIZATION_ID = "cssa"
SEASON = "2026-2027"

CASE_FIXTURE_CHANGE = "fixture_change"
CASE_FMI = "fmi"
CASE_OFFICIAL_CORRESPONDENCE = "official_correspondence"
CASE_CLUB_INFO_UPDATE = "club_info_update"

CHANNEL_FOOTCLUBS = "FOOTCLUBS"
CHANNEL_OFFICIAL_EMAIL = "OFFICIAL_EMAIL"
CHANNEL_FMI = "FMI"
CHANNEL_PAPER_FALLBACK = "PAPER_FALLBACK"

AUTHORITY_CSSA = "CSSA"
AUTHORITY_LGEF_COMPETITIONS = "LGEF_COMPETITIONS_WITH_CRC"
AUTHORITY_LGEF_COMMISSION = "LGEF_COMMISSION"
AUTHORITY_CRA = "LGEF_CRA"


@dataclass(frozen=True)
class CSSAPublicAdminAssessmentV0:
    case_type: str
    case_ref: str
    valid_at: str
    required_channel: str | None
    responsible_role: str | None
    final_authority: str | None
    status_candidate: str
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    human_validation_required: bool = True
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    decision_authority: str = "KX108_ONLY"

    def __post_init__(self) -> None:
        if not self.case_type:
            raise ValueError("case_type is required")
        if not self.case_ref:
            raise ValueError("case_ref is required")
        if not self.valid_at:
            raise ValueError("valid_at is required")
        if self.decision_authority != "KX108_ONLY":
            raise ValueError("decision authority must remain KX108_ONLY")
        if self.allowed_to_decide:
            raise ValueError("CSSA public assessment cannot decide")
        if self.allowed_to_act:
            raise ValueError("CSSA public assessment cannot act")

    def to_domain_state_ref(self) -> DomainStateRefV0:
        return DomainStateRefV0(
            domain_id=DOMAIN_ID,
            state_ref=f"cssa:{self.case_type}:{self.case_ref}",
            valid_at=self.valid_at,
            upstream_state_ref=f"cssa-public:{self.case_ref}",
            unknowns=self.unknowns,
            contradictions=self.contradictions,
            risk_flags=self.risk_flags,
            evidence_refs=self.evidence_refs,
            provenance_refs=self.provenance_refs,
        )

    def to_runtime_mapping(self, *, confidence: float) -> dict[str, Any]:
        """Return adapter input for the portable Administration runtime.

        CSSA-specific business fields remain local and are not part of the
        universal GovernancePayload contract.
        """
        return {
            "case_ref": f"cssa:{self.case_type}:{self.case_ref}",
            "valid_at": self.valid_at,
            "source_ref": f"cssa-public:{self.case_ref}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": self.evidence_refs,
            "provenance_refs": self.provenance_refs,
            "confidence": float(confidence),
            "cssa_case_type": self.case_type,
            "required_channel": self.required_channel,
            "responsible_role": self.responsible_role,
            "final_authority": self.final_authority,
            "status_candidate": self.status_candidate,
            "human_validation_required": self.human_validation_required,
        }


def cssa_public_case_adapter(raw: Mapping[str, Any]) -> DomainStateRefV0:
    """CSSA organization-pack adapter -> generic Administration state."""
    return DomainStateRefV0(
        domain_id=DOMAIN_ID,
        state_ref=str(raw["case_ref"]),
        valid_at=str(raw["valid_at"]),
        upstream_state_ref=raw.get("source_ref"),
        unknowns=tuple(str(v) for v in raw.get("unknowns", ()) or ()),
        contradictions=tuple(
            str(v) for v in raw.get("contradictions", ()) or ()
        ),
        risk_flags=tuple(str(v) for v in raw.get("risk_flags", ()) or ()),
        evidence_refs=tuple(
            str(v) for v in raw.get("evidence_refs", ()) or ()
        ),
        provenance_refs=tuple(
            str(v) for v in raw.get("provenance_refs", ()) or ()
        ),
    )


def assess_fixture_change(
    *,
    case_ref: str,
    valid_at: str,
    days_before_match: int,
    via_footclubs: bool,
    official_email_agreement: bool,
    homologated_by_lgef: bool | None,
) -> CSSAPublicAdminAssessmentV0:
    """Public LGEF 2026/27 article 20.7 candidate workflow."""

    unknowns: list[str] = []
    contradictions: list[str] = []
    risk_flags: list[str] = []

    if days_before_match >= 10:
        required_channel = CHANNEL_FOOTCLUBS
        if not via_footclubs:
            risk_flags.append("FIXTURE_CHANGE_NOT_VIA_FOOTCLUBS")
        status = "NORMAL_WINDOW"
    else:
        required_channel = CHANNEL_OFFICIAL_EMAIL
        status = "LATE_WINDOW"
        if not official_email_agreement:
            risk_flags.append("LATE_CHANGE_CLUB_AGREEMENT_MISSING")

    # In both routes, CSSA cannot self-homologate the fixture.
    if homologated_by_lgef is None:
        unknowns.append("LGEF_HOMOLOGATION_UNKNOWN")
    elif homologated_by_lgef is False:
        risk_flags.append("FIXTURE_CHANGE_NOT_HOMOLOGATED")

    return CSSAPublicAdminAssessmentV0(
        case_type=CASE_FIXTURE_CHANGE,
        case_ref=case_ref,
        valid_at=valid_at,
        required_channel=required_channel,
        responsible_role="CSSA_ADMINISTRATION",
        final_authority=AUTHORITY_LGEF_COMPETITIONS,
        status_candidate=status,
        unknowns=tuple(unknowns),
        contradictions=tuple(contradictions),
        risk_flags=tuple(risk_flags),
        evidence_refs=("LGEF_2026_2027_ART_20_7",),
        provenance_refs=(
            "LGEF_REGLEMENTS_PARTICULIERS_2026_2027",
            "CSSA_PUBLIC_ORGANIZATION",
        ),
    )


def assess_fmi(
    *,
    case_ref: str,
    valid_at: str,
    cssa_is_receiving_club: bool,
    fmi_available: bool,
    transmitted_by_next_day_10: bool | None,
    paper_fallback_sent_in_time: bool | None = None,
) -> CSSAPublicAdminAssessmentV0:
    """Public LGEF 2026/27 article 24 candidate workflow."""

    unknowns: list[str] = []
    risk_flags: list[str] = []

    if not cssa_is_receiving_club:
        return CSSAPublicAdminAssessmentV0(
            case_type=CASE_FMI,
            case_ref=case_ref,
            valid_at=valid_at,
            required_channel=None,
            responsible_role=None,
            final_authority=AUTHORITY_LGEF_COMMISSION,
            status_candidate="CSSA_NOT_RECEIVING_CLUB",
            evidence_refs=("LGEF_2026_2027_ART_24",),
            provenance_refs=("LGEF_REGLEMENTS_PARTICULIERS_2026_2027",),
        )

    if fmi_available:
        required_channel = CHANNEL_FMI
        status = "FMI_NORMAL_PATH"
        if transmitted_by_next_day_10 is None:
            unknowns.append("FMI_TRANSMISSION_STATUS_UNKNOWN")
        elif transmitted_by_next_day_10 is False:
            risk_flags.append("FMI_TRANSMISSION_DEADLINE_MISSED")
    else:
        required_channel = CHANNEL_PAPER_FALLBACK
        status = "FMI_EXCEPTION_PAPER_FALLBACK"
        risk_flags.append("FMI_TECHNICAL_EXCEPTION_REQUIRES_COMMISSION_REVIEW")
        if paper_fallback_sent_in_time is None:
            unknowns.append("PAPER_FALLBACK_TRANSMISSION_STATUS_UNKNOWN")
        elif paper_fallback_sent_in_time is False:
            risk_flags.append("PAPER_FALLBACK_DEADLINE_MISSED")

    return CSSAPublicAdminAssessmentV0(
        case_type=CASE_FMI,
        case_ref=case_ref,
        valid_at=valid_at,
        required_channel=required_channel,
        responsible_role="CSSA_RECEIVING_CLUB_ADMINISTRATION",
        final_authority=AUTHORITY_LGEF_COMMISSION,
        status_candidate=status,
        unknowns=tuple(unknowns),
        risk_flags=tuple(risk_flags),
        evidence_refs=("LGEF_2026_2027_ART_24",),
        provenance_refs=("LGEF_REGLEMENTS_PARTICULIERS_2026_2027",),
    )


def assess_official_correspondence(
    *,
    case_ref: str,
    valid_at: str,
    outbound_to_lgef_or_district: bool,
    sent_from_official_club_address: bool | None,
) -> CSSAPublicAdminAssessmentV0:
    """Public LGEF Article 1 correspondence rule."""

    unknowns: list[str] = []
    risk_flags: list[str] = []

    if outbound_to_lgef_or_district:
        if sent_from_official_club_address is None:
            unknowns.append("OFFICIAL_SENDER_ADDRESS_UNKNOWN")
        elif sent_from_official_club_address is False:
            risk_flags.append("NON_OFFICIAL_SENDER_ADDRESS")

    return CSSAPublicAdminAssessmentV0(
        case_type=CASE_OFFICIAL_CORRESPONDENCE,
        case_ref=case_ref,
        valid_at=valid_at,
        required_channel=CHANNEL_OFFICIAL_EMAIL,
        responsible_role="CSSA_ADMINISTRATION",
        final_authority=None,
        status_candidate="OFFICIAL_CORRESPONDENCE_CHECK",
        unknowns=tuple(unknowns),
        risk_flags=tuple(risk_flags),
        evidence_refs=("LGEF_2026_2027_ART_1_CORRESPONDENCE",),
        provenance_refs=(
            "LGEF_REGLEMENTS_PARTICULIERS_2026_2027",
            "CSSA_PUBLIC_CONTACT_PAGE",
        ),
    )


def assess_club_info_update(
    *,
    case_ref: str,
    valid_at: str,
    days_since_change: int,
    notified_lgef: bool | None,
) -> CSSAPublicAdminAssessmentV0:
    """Public LGEF Article 3.3 update-within-10-days candidate."""

    unknowns: list[str] = []
    risk_flags: list[str] = []

    if notified_lgef is None:
        unknowns.append("LGEF_NOTIFICATION_STATUS_UNKNOWN")
    elif not notified_lgef and days_since_change > 10:
        risk_flags.append("CLUB_INFORMATION_UPDATE_DEADLINE_MISSED")
    elif not notified_lgef:
        risk_flags.append("CLUB_INFORMATION_UPDATE_PENDING")

    return CSSAPublicAdminAssessmentV0(
        case_type=CASE_CLUB_INFO_UPDATE,
        case_ref=case_ref,
        valid_at=valid_at,
        required_channel=CHANNEL_OFFICIAL_EMAIL,
        responsible_role="CSSA_SECRETARIAT_OR_ADMINISTRATION",
        final_authority=None,
        status_candidate="CLUB_INFORMATION_UPDATE",
        unknowns=tuple(unknowns),
        risk_flags=tuple(risk_flags),
        evidence_refs=("LGEF_2026_2027_ART_3_3",),
        provenance_refs=("LGEF_REGLEMENTS_PARTICULIERS_2026_2027",),
    )
