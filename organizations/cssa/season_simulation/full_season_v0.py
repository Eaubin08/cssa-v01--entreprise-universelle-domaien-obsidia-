"""F3E — deterministic full-season CSSA simulator V0.

Synthetic only. No event in this module is evidence of real CSSA internal practice.

The generator uses the F3D public/estimated scale model to create a long-running
organization workload across all 19 public team structures and club-wide
administrative domains.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any, Iterable, Mapping


SIMULATION_STATUS = "SIMULATED_NOT_OBSERVED"
HIGH_SENSITIVITY = {"MINOR_DATA", "HEALTH_DATA", "DISCIPLINARY_DATA", "FINANCIAL_DATA"}

FIXTURE_COUNTS_V0 = {
    "SENIORS_R1": 26,
    "SENIORS_R2": 22,
    "U20_R1": 22,
    "U17_R1": 22,
    "U16_R1": 22,
    "U15_R1": 22,
    "U15_D1": 18,
    "SENIORS_F": 18,
    "U18F_R2": 18,
    "U13_FANION": 18,
    "U13_U12_ESPOIR": 16,
    "U12_AVENIR": 16,
    "U11_FANION": 14,
    "U11_U10_ESPOIR": 14,
    "U10_AVENIR": 14,
    "U9": 12,
    "U8": 12,
    "U7": 12,
    "U6": 12,
}

FMI_TEAMS = {"SENIORS_R1", "SENIORS_R2", "U20_R1"}


@dataclass(frozen=True)
class CSSASeasonEventV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    source_ids: tuple[str, ...]
    team_id: str | None = None
    target_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    sensitivity: tuple[str, ...] = ("INTERNAL",)
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ("F3E_SIMULATION_ONLY",)
    estimated_amount_eur: float | None = None
    estimated_team_route_km: float | None = None
    simulation_status: str = SIMULATION_STATUS

    def __post_init__(self) -> None:
        if self.simulation_status != SIMULATION_STATUS:
            raise ValueError("F3E events must remain explicitly simulated")
        if not self.event_id or not self.event_date or not self.family:
            raise ValueError("event identity/date/family are required")
        if self.estimated_amount_eur is not None and self.estimated_amount_eur < 0:
            raise ValueError("estimated_amount_eur must be >= 0")
        if self.estimated_team_route_km is not None and self.estimated_team_route_km < 0:
            raise ValueError("estimated_team_route_km must be >= 0")

    @property
    def privacy_blocked(self) -> bool:
        return bool(set(self.sensitivity) & HIGH_SENSITIVITY)

    @property
    def expected_gate(self) -> str:
        if self.privacy_blocked:
            return "PRE_RUNTIME_BLOCK"
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"

    @property
    def expected_provider_invoked(self) -> bool:
        return self.expected_gate == "ALLOW"

    def to_runtime_mapping(self, *, confidence: float = 0.92) -> dict[str, Any]:
        if self.privacy_blocked:
            raise ValueError(f"PRIVACY_BLOCKED_BEFORE_RUNTIME:{self.event_id}")
        return {
            "case_ref": f"cssa-season-sim:{self.event_id}",
            "valid_at": f"{self.event_date}T12:00:00Z",
            "source_ref": f"cssa-season-sim-source:{self.event_id}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": tuple(dict.fromkeys((*self.source_ids, *self.evidence_refs))),
            "provenance_refs": self.provenance_refs,
            "confidence": float(confidence),
            "simulation_status": self.simulation_status,
            "event_family": self.family,
            "team_id": self.team_id,
            "estimated_amount_eur": self.estimated_amount_eur,
            "estimated_team_route_km": self.estimated_team_route_km,
        }


@dataclass(frozen=True)
class CSSASeasonCorpusV0:
    start_date: str
    end_date: str
    events: tuple[CSSASeasonEventV0, ...]
    simulation_status: str = SIMULATION_STATUS

    def __post_init__(self) -> None:
        if self.simulation_status != SIMULATION_STATUS:
            raise ValueError("corpus must remain simulated")

    def by_gate(self, gate: str) -> tuple[CSSASeasonEventV0, ...]:
        return tuple(e for e in self.events if e.expected_gate == gate)

    def by_family(self, family: str) -> tuple[CSSASeasonEventV0, ...]:
        return tuple(e for e in self.events if e.family == family)

    def by_team(self, team_id: str) -> tuple[CSSASeasonEventV0, ...]:
        return tuple(e for e in self.events if e.team_id == team_id)

    @property
    def team_ids(self) -> tuple[str, ...]:
        return tuple(sorted({e.team_id for e in self.events if e.team_id}))

    @property
    def total_estimated_team_route_km(self) -> float:
        """Count planned away trips once; reconciliation events are proof, not new travel."""
        return round(
            sum(
                e.estimated_team_route_km or 0.0
                for e in self.events
                if e.case_type == "away_trip_plan"
            ),
            2,
        )


def _spread_dates(count: int, start: date, end: date, offset_days: int) -> list[date]:
    if count <= 0:
        return []
    span = max(1, (end - start).days)
    if count == 1:
        return [start + timedelta(days=min(offset_days, span))]
    step = span / (count - 1)
    dates = []
    for i in range(count):
        day = min(span, int(round(i * step)) + offset_days)
        dates.append(start + timedelta(days=day))
    return dates


def _route_km_for_team(public_model: Mapping[str, Any], team_id: str) -> float:
    ranges = public_model["travel_estimates"]["team_route_km_ranges"]
    if team_id in ranges:
        low, high = ranges[team_id]
        # Approximate total seasonal away-route km for this team.
        return (float(low) + float(high)) / 2.0
    if team_id in {"U11_FANION", "U11_U10_ESPOIR", "U10_AVENIR", "U9", "U8", "U7", "U6"}:
        low, high = ranges["U6_U11_COLLECTIVE"]
        # Shared collective range divided across seven structures.
        return ((float(low) + float(high)) / 2.0) / 7.0
    return 0.0


def _inject_anomaly(event: CSSASeasonEventV0, ordinal: int) -> CSSASeasonEventV0:
    """Deterministic anomaly injection for stress testing.

    This never claims such anomaly occurred at CSSA.
    """
    if event.family in {"PRIVACY_SENSITIVE", "SEASON_CONTROL"}:
        return event

    # BLOCK has precedence in real Guard if two contradictions exist.
    if ordinal % 31 == 0:
        return replace(
            event,
            contradictions=(
                "SIMULATED_SOURCE_CONTRADICTION_A",
                "SIMULATED_SOURCE_CONTRADICTION_B",
            ),
            risk_flags=tuple(dict.fromkeys((*event.risk_flags, "SIMULATED_STALE_STATE"))),
        )

    # HOLD requires >1 unknown under current Guard.
    if ordinal % 23 == 0:
        return replace(
            event,
            unknowns=(
                "SIMULATED_REQUIRED_FACT_UNKNOWN_A",
                "SIMULATED_REQUIRED_FACT_UNKNOWN_B",
            ),
        )

    return event


def build_full_season_corpus_v0(public_model: Mapping[str, Any]) -> CSSASeasonCorpusV0:
    """Build a deterministic synthetic 2026-2027 whole-club season."""
    start = date(2026, 8, 1)
    competition_start = date(2026, 8, 22)
    competition_end = date(2027, 5, 30)
    end = date(2027, 6, 15)

    team_ids = [team["id"] for team in public_model["organization"]["teams"]]
    if set(team_ids) != set(FIXTURE_COUNTS_V0):
        raise ValueError("PUBLIC_TEAM_SET_AND_SIMULATION_PROFILE_DIVERGE")

    events: list[CSSASeasonEventV0] = []

    # Pre-season: registration + equipment readiness for all 19 structures.
    for team_index, team_id in enumerate(team_ids, start=1):
        d0 = start + timedelta(days=team_index % 14)
        events.append(
            CSSASeasonEventV0(
                event_id=f"LICENCE-{team_id}",
                event_date=d0.isoformat(),
                family="ACADEMY_MEMBERSHIP",
                case_type="licence_roster_readiness",
                team_id=team_id,
                source_ids=(f"sim:licence-roster:{team_id}",),
                target_refs=(f"team:{team_id}",),
                evidence_refs=("CSSA_LICENSE_2026_2027",),
            )
        )
        events.append(
            CSSASeasonEventV0(
                event_id=f"EQUIPMENT-{team_id}",
                event_date=(d0 + timedelta(days=3)).isoformat(),
                family="ACADEMY_MEMBERSHIP",
                case_type="equipment_order_readiness",
                team_id=team_id,
                source_ids=(f"sim:equipment-order:{team_id}",),
                target_refs=(f"team:{team_id}",),
                evidence_refs=("CSSA_LICENSE_2026_2027",),
                risk_flags=("PERSONALIZED_EQUIPMENT_NON_EXCHANGEABLE",),
            )
        )

    # Season fixtures across all public team structures.
    for team_index, team_id in enumerate(team_ids):
        fixture_count = FIXTURE_COUNTS_V0[team_id]
        fixture_dates = _spread_dates(
            fixture_count,
            competition_start,
            competition_end,
            offset_days=team_index % 5,
        )
        season_route_km = _route_km_for_team(public_model, team_id)
        away_count = fixture_count // 2
        km_per_away = season_route_km / away_count if away_count else 0.0

        for fixture_index, fixture_date in enumerate(fixture_dates, start=1):
            is_away = fixture_index % 2 == 0
            venue = "AWAY" if is_away else "HOME"
            fixture_ref = f"fixture:{team_id}:{fixture_index:02d}"

            events.append(
                CSSASeasonEventV0(
                    event_id=f"FIXTURE-{team_id}-{fixture_index:02d}",
                    event_date=fixture_date.isoformat(),
                    family="COMPETITIONS",
                    case_type="fixture_state",
                    team_id=team_id,
                    source_ids=(f"sim:competition-state:{fixture_ref}",),
                    target_refs=(fixture_ref,),
                    evidence_refs=("F3D_SEASON_PUBLIC_MODEL",),
                    risk_flags=(f"{venue}_MATCH",),
                )
            )

            if is_away:
                events.append(
                    CSSASeasonEventV0(
                        event_id=f"TRAVEL-PLAN-{team_id}-{fixture_index:02d}",
                        event_date=(fixture_date - timedelta(days=7)).isoformat(),
                        family="TRAVEL_LOGISTICS",
                        case_type="away_trip_plan",
                        team_id=team_id,
                        source_ids=(f"sim:travel-plan:{fixture_ref}",),
                        target_refs=(fixture_ref,),
                        estimated_team_route_km=km_per_away,
                        risk_flags=("SIMULATION_ROUTE_ESTIMATE",),
                    )
                )
                events.append(
                    CSSASeasonEventV0(
                        event_id=f"TRAVEL-CLOSE-{team_id}-{fixture_index:02d}",
                        event_date=(fixture_date + timedelta(days=2)).isoformat(),
                        family="FINANCE_ACCOUNTING",
                        case_type="travel_reconciliation",
                        team_id=team_id,
                        source_ids=(f"sim:travel-close:{fixture_ref}",),
                        target_refs=(fixture_ref,),
                        estimated_team_route_km=km_per_away,
                        risk_flags=("SIMULATION_COST_NOT_ACCOUNTING_FACT",),
                    )
                )

            if team_id in FMI_TEAMS:
                events.append(
                    CSSASeasonEventV0(
                        event_id=f"FMI-{team_id}-{fixture_index:02d}",
                        event_date=(fixture_date + timedelta(days=1)).isoformat(),
                        family="COMPETITIONS",
                        case_type="fmi_post_match",
                        team_id=team_id,
                        source_ids=(f"sim:fmi:{fixture_ref}",),
                        target_refs=(fixture_ref,),
                        evidence_refs=("LGEF_2026_2027_ART_24",),
                    )
                )

            if team_id == "SENIORS_R1":
                events.append(
                    CSSASeasonEventV0(
                        event_id=f"COMM-{team_id}-{fixture_index:02d}",
                        event_date=(fixture_date - timedelta(days=2)).isoformat(),
                        family="COMMUNICATION",
                        case_type="match_publication_candidate",
                        team_id=team_id,
                        source_ids=(f"sim:publication:{fixture_ref}",),
                        target_refs=(fixture_ref,),
                        risk_flags=("SUPPORTER_OUTPUT_REQUIRES_CURRENT_MATCH_STATE",),
                    )
                )

                if not is_away:
                    events.extend(
                        (
                            CSSASeasonEventV0(
                                event_id=f"MATCHDAY-{team_id}-{fixture_index:02d}",
                                event_date=(fixture_date - timedelta(days=1)).isoformat(),
                                family="MATCHDAY",
                                case_type="venue_configuration",
                                team_id=team_id,
                                source_ids=(f"sim:venue:{fixture_ref}",),
                                target_refs=(fixture_ref,),
                            ),
                            CSSASeasonEventV0(
                                event_id=f"PARTNER-{team_id}-{fixture_index:02d}",
                                event_date=(fixture_date - timedelta(days=4)).isoformat(),
                                family="PARTNERS_COMMERCIAL",
                                case_type="hospitality_activation",
                                team_id=team_id,
                                source_ids=(f"sim:partner-hospitality:{fixture_ref}",),
                                target_refs=(fixture_ref,),
                                risk_flags=("PARTNER_CONTRACT_VALUE_UNKNOWN_PRIVATE",),
                            ),
                            CSSASeasonEventV0(
                                event_id=f"VOLUNTEER-{team_id}-{fixture_index:02d}",
                                event_date=(fixture_date - timedelta(days=3)).isoformat(),
                                family="PEOPLE_HR_VOLUNTEERS",
                                case_type="matchday_volunteer_assignment",
                                team_id=team_id,
                                source_ids=(f"sim:volunteer-plan:{fixture_ref}",),
                                target_refs=(fixture_ref,),
                            ),
                            CSSASeasonEventV0(
                                event_id=f"TICKETING-{team_id}-{fixture_index:02d}",
                                event_date=(fixture_date - timedelta(days=5)).isoformat(),
                                family="SUPPORTERS_TICKETING",
                                case_type="home_match_ticketing_state",
                                team_id=team_id,
                                source_ids=(f"sim:ticketing:{fixture_ref}",),
                                target_refs=(fixture_ref,),
                                risk_flags=("PRODUCT_MIX_UNKNOWN_PRIVATE",),
                            ),
                        )
                    )

    # Monthly whole-club operating cadence.
    month_cursor = date(2026, 8, 15)
    month_index = 1
    while month_cursor <= date(2027, 5, 15):
        events.extend(
            (
                CSSASeasonEventV0(
                    event_id=f"FINANCE-CLOSE-{month_index:02d}",
                    event_date=month_cursor.isoformat(),
                    family="FINANCE_ACCOUNTING",
                    case_type="monthly_close",
                    source_ids=(f"sim:finance-close:{month_index:02d}",),
                    risk_flags=("SIMULATION_LEDGER_ONLY",),
                ),
                CSSASeasonEventV0(
                    event_id=f"PARTNER-REVIEW-{month_index:02d}",
                    event_date=(month_cursor + timedelta(days=1)).isoformat(),
                    family="PARTNERS_COMMERCIAL",
                    case_type="partner_commitment_review",
                    source_ids=(f"sim:partner-review:{month_index:02d}",),
                    risk_flags=("PARTNER_REVENUE_UNKNOWN_PRIVATE",),
                ),
                CSSASeasonEventV0(
                    event_id=f"SOURCE-FRESHNESS-{month_index:02d}",
                    event_date=(month_cursor + timedelta(days=2)).isoformat(),
                    family="PROOF_AUDIT",
                    case_type="public_source_freshness_check",
                    source_ids=(f"sim:source-freshness:{month_index:02d}",),
                    evidence_refs=("F3D_PUBLIC_SOURCE_COHERENCE_FINDINGS",),
                ),
                CSSASeasonEventV0(
                    event_id=f"DELEGATION-{month_index:02d}",
                    event_date=(month_cursor + timedelta(days=3)).isoformat(),
                    family="PEOPLE_HR_VOLUNTEERS",
                    case_type="responsibility_delegation_review",
                    source_ids=(f"sim:delegation:{month_index:02d}",),
                    risk_flags=("ROLE_OCCUPANT_CAN_CHANGE",),
                ),
                CSSASeasonEventV0(
                    event_id=f"EDUCATION-{month_index:02d}",
                    event_date=(month_cursor + timedelta(days=4)).isoformat(),
                    family="EDUCATION",
                    case_type="school_sport_coordination_summary",
                    source_ids=(f"sim:education-summary:{month_index:02d}",),
                    sensitivity=("INTERNAL",),
                ),
            )
        )
        if month_cursor.month == 12:
            month_cursor = date(2027, 1, 15)
        else:
            next_month = month_cursor.month + 1
            year = month_cursor.year
            if next_month == 13:
                next_month = 1
                year += 1
            month_cursor = date(year, next_month, 15)
        month_index += 1

    # Explicit rare cross-cutting stress cases.
    events.extend(
        (
            CSSASeasonEventV0(
                event_id="STRESS-MANAGER-VACANCY",
                event_date="2026-09-11",
                family="PEOPLE_HR_VOLUNTEERS",
                case_type="management_vacancy_continuity",
                source_ids=("sim:manager-vacancy",),
                unknowns=(
                    "INTERIM_DELEGATION_UNKNOWN",
                    "SIGNATURE_AUTHORITY_UNKNOWN",
                ),
                evidence_refs=("CSSA_MANAGER_DEPARTURE_2026_09_10",),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-SOURCE-STALE",
                event_date="2026-09-15",
                family="PROOF_AUDIT",
                case_type="public_source_contradiction",
                source_ids=("sim:organigramme", "sim:departure-communique"),
                contradictions=(
                    "MANAGER_OCCUPANT_SOURCE_CONFLICT",
                    "SOURCE_FRESHNESS_CONFLICT",
                ),
                evidence_refs=("STALE_MANAGER_GENERAL",),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-LATE-FIXTURE-CHANGE",
                event_date="2026-10-20",
                family="COMPETITIONS",
                case_type="late_fixture_change",
                source_ids=("sim:late-request",),
                unknowns=(
                    "OTHER_CLUB_AGREEMENT_UNKNOWN",
                    "LGEF_HOMOLOGATION_UNKNOWN",
                ),
                evidence_refs=("LGEF_2026_2027_ART_20_7",),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-FMI-FAILURE",
                event_date="2026-11-09",
                family="COMPETITIONS",
                case_type="fmi_technical_exception",
                source_ids=("sim:fmi-failure", "sim:paper-fallback"),
                unknowns=(
                    "PAPER_FALLBACK_TRANSMISSION_UNKNOWN",
                    "COMMISSION_REVIEW_STATUS_UNKNOWN",
                ),
                evidence_refs=("LGEF_2026_2027_ART_24",),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-YOUTH-HEALTH",
                event_date="2027-01-20",
                family="PRIVACY_SENSITIVE",
                case_type="youth_health_record",
                source_ids=("sim:youth-health-record",),
                sensitivity=("INTERNAL", "MINOR_DATA", "HEALTH_DATA"),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-PAYROLL",
                event_date="2027-02-28",
                family="PRIVACY_SENSITIVE",
                case_type="employee_payroll_record",
                source_ids=("sim:payroll-record",),
                sensitivity=("INTERNAL", "FINANCIAL_DATA"),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-PARTNER-INVOICE",
                event_date="2027-03-15",
                family="PARTNERS_COMMERCIAL",
                case_type="partner_invoice_missing_contract_value",
                source_ids=("sim:partner-invoice",),
                unknowns=(
                    "PARTNER_CONTRACT_TIER_UNKNOWN",
                    "PARTNER_COMMITMENT_VALUE_UNKNOWN",
                ),
            ),
            CSSASeasonEventV0(
                event_id="STRESS-SUBSCRIBER-REVENUE",
                event_date="2026-08-30",
                family="SUPPORTERS_TICKETING",
                case_type="subscriber_revenue_inference_attempt",
                source_ids=("sim:subscriber-count",),
                unknowns=(
                    "SUBSCRIPTION_PRODUCT_MIX_UNKNOWN",
                    "PARTNER_INCLUDED_COUNT_UNKNOWN_SPLIT",
                ),
                risk_flags=("DO_NOT_INFER_REVENUE_FROM_COUNT",),
            ),
        )
    )

    # Inject deterministic distributed anomalies after constructing the workload.
    events = [_inject_anomaly(event, i) for i, event in enumerate(events, start=1)]
    events.sort(key=lambda e: (e.event_date, e.event_id))

    return CSSASeasonCorpusV0(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        events=tuple(events),
    )


def corpus_summary_v0(corpus: CSSASeasonCorpusV0) -> dict[str, Any]:
    families: dict[str, int] = {}
    gates: dict[str, int] = {}
    for event in corpus.events:
        families[event.family] = families.get(event.family, 0) + 1
        gates[event.expected_gate] = gates.get(event.expected_gate, 0) + 1
    return {
        "simulation_status": corpus.simulation_status,
        "start_date": corpus.start_date,
        "end_date": corpus.end_date,
        "event_count": len(corpus.events),
        "team_count": len(corpus.team_ids),
        "family_counts": dict(sorted(families.items())),
        "gate_counts": dict(sorted(gates.items())),
        "estimated_team_route_km": corpus.total_estimated_team_route_km,
    }
