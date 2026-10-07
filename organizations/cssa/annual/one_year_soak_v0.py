"""F3H — one-year longitudinal soak/failure campaign V0.

Purpose:
- run the CSSA organization model continuously for 365 days;
- preserve backlog and unresolved state across days;
- inject deterministic capacity outages;
- measure deadline misses, starvation, unresolved HOLD/BLOCK aging,
  shared-asset collisions, travel-budget pressure and backlog saturation.

All outputs are synthetic failure signals, not claims about real CSSA failures.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

from organizations.cssa.season_simulation import (
    CSSASeasonEventV0,
    build_full_season_corpus_v0,
)


STATUS = "SIMULATED_ONE_YEAR_SOAK"
TRUTH_CLASS = "SIMULATED_NOT_OBSERVED"

FAMILY_DEADLINE_DAYS = {
    "COMPETITIONS": 1,
    "MATCHDAY": 1,
    "COMMUNICATION": 1,
    "SUPPORTERS_TICKETING": 2,
    "TRAVEL_LOGISTICS": 3,
    "FINANCE_ACCOUNTING": 5,
    "PARTNERS_COMMERCIAL": 5,
    "ACADEMY_MEMBERSHIP": 7,
    "PEOPLE_HR_VOLUNTEERS": 5,
    "EDUCATION": 7,
    "PROOF_AUDIT": 4,
    "FACILITIES": 5,
    "GOVERNANCE_LEGAL": 3,
    "PRIVACY_SENSITIVE": 0,
}

FAMILY_PRIORITY = {
    "MATCHDAY": 100,
    "COMPETITIONS": 90,
    "GOVERNANCE_LEGAL": 85,
    "PROOF_AUDIT": 75,
    "TRAVEL_LOGISTICS": 70,
    "SUPPORTERS_TICKETING": 65,
    "PEOPLE_HR_VOLUNTEERS": 60,
    "FINANCE_ACCOUNTING": 55,
    "PARTNERS_COMMERCIAL": 50,
    "COMMUNICATION": 45,
    "ACADEMY_MEMBERSHIP": 40,
    "FACILITIES": 40,
    "EDUCATION": 30,
}

ASSET_DEMAND_BY_CASE = {
    "away_trip_plan": ("VEHICLE_EQUIVALENT_POOL", 1.0),
    "hospitality_activation": ("HOSPITALITY_SPACE", 1.0),
    "venue_configuration": ("MAIN_STADIUM_SLOT", 1.0),
    "matchday_volunteer_assignment": ("VOLUNTEER_MATCHDAY_POOL", 12.0),
}


@dataclass(frozen=True)
class AnnualCaseV0:
    case_id: str
    arrival_date: date
    due_date: date
    family: str
    case_type: str
    initial_gate: str
    role_demands: tuple[tuple[str, float], ...]
    asset_demand: tuple[str, float] | None
    estimated_travel_cost_eur: float
    priority_score: int
    source_event: Any


@dataclass(frozen=True)
class FailureSignalV0:
    day: str
    failure_type: str
    severity: str
    case_id: str | None
    resource_id: str | None
    detail: str
    truth_class: str = TRUTH_CLASS


@dataclass(frozen=True)
class AnnualRunResultV0:
    profile_id: str
    attack_mode: str
    start_date: str
    end_date: str
    day_count: int
    input_event_count: int
    completed_case_count: int
    pending_case_count: int
    privacy_manual_review_count: int
    failure_signals: tuple[FailureSignalV0, ...]
    max_backlog: int
    max_case_age_days: int
    monthly_travel_costs: tuple[tuple[str, float], ...]
    status: str = STATUS

    def __post_init__(self) -> None:
        if self.status != STATUS:
            raise ValueError("ONE_YEAR_SOAK_STATUS_REQUIRED")


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_one_year_corpus_v0(public_model: Mapping[str, Any]) -> tuple[Any, ...]:
    """Extend the F3E season through 2027-07-31 with off-season transition work."""
    base = build_full_season_corpus_v0(public_model)
    events = list(base.events)

    transition = [
        CSSASeasonEventV0(
            event_id="YEAR-END-FINANCE-CLOSE",
            event_date="2027-06-20",
            family="FINANCE_ACCOUNTING",
            case_type="annual_finance_close_preparation",
            source_ids=("sim:annual-finance-close",),
            risk_flags=("SIMULATION_LEDGER_ONLY",),
        ),
        CSSASeasonEventV0(
            event_id="YEAR-END-PARTNER-RENEWAL",
            event_date="2027-06-22",
            family="PARTNERS_COMMERCIAL",
            case_type="partner_renewal_campaign",
            source_ids=("sim:partner-renewal",),
            risk_flags=("PARTNER_CONTRACT_VALUE_UNKNOWN_PRIVATE",),
        ),
        CSSASeasonEventV0(
            event_id="YEAR-END-STAFF-REVIEW",
            event_date="2027-06-24",
            family="PEOPLE_HR_VOLUNTEERS",
            case_type="staffing_and_delegation_review",
            source_ids=("sim:staff-review",),
        ),
        CSSASeasonEventV0(
            event_id="YEAR-END-FACILITY-REVIEW",
            event_date="2027-06-26",
            family="FACILITIES",
            case_type="facility_preseason_readiness",
            source_ids=("sim:facility-review",),
        ),
        CSSASeasonEventV0(
            event_id="YEAR-END-SOURCE-AUDIT",
            event_date="2027-06-28",
            family="PROOF_AUDIT",
            case_type="annual_source_freshness_audit",
            source_ids=("sim:annual-source-audit",),
        ),
        CSSASeasonEventV0(
            event_id="YEAR-END-GOVERNANCE-REVIEW",
            event_date="2027-06-30",
            family="GOVERNANCE_LEGAL",
            case_type="season_governance_review",
            source_ids=("sim:season-governance-review",),
            unknowns=("NEXT_SEASON_DELEGATIONS_NOT_FINAL", "NEXT_SEASON_BUDGET_NOT_FINAL"),
        ),
        CSSASeasonEventV0(
            event_id="PRESEASON-SUBSCRIPTION-LAUNCH",
            event_date="2027-07-01",
            family="SUPPORTERS_TICKETING",
            case_type="next_season_subscription_preparation",
            source_ids=("sim:subscription-launch",),
        ),
        CSSASeasonEventV0(
            event_id="PRESEASON-COMM-LAUNCH",
            event_date="2027-07-03",
            family="COMMUNICATION",
            case_type="next_season_publication_plan",
            source_ids=("sim:preseason-communication",),
        ),
    ]

    team_ids = [team["id"] for team in public_model["organization"]["teams"]]
    for index, team_id in enumerate(team_ids):
        day = 2 + (index % 12)
        events.extend(
            (
                CSSASeasonEventV0(
                    event_id=f"PRESEASON-LICENCE-{team_id}",
                    event_date=f"2027-07-{day:02d}",
                    family="ACADEMY_MEMBERSHIP",
                    case_type="next_season_licence_readiness",
                    team_id=team_id,
                    source_ids=(f"sim:preseason-licence:{team_id}",),
                ),
                CSSASeasonEventV0(
                    event_id=f"PRESEASON-EQUIPMENT-{team_id}",
                    event_date=f"2027-07-{min(day + 5, 28):02d}",
                    family="ACADEMY_MEMBERSHIP",
                    case_type="next_season_equipment_readiness",
                    team_id=team_id,
                    source_ids=(f"sim:preseason-equipment:{team_id}",),
                ),
                CSSASeasonEventV0(
                    event_id=f"PRESEASON-SCHEDULE-{team_id}",
                    event_date=f"2027-07-{min(day + 10, 30):02d}",
                    family="COMPETITIONS",
                    case_type="next_season_schedule_readiness",
                    team_id=team_id,
                    source_ids=(f"sim:preseason-schedule:{team_id}",),
                    unknowns=(
                        ("FINAL_GROUP_OR_CALENDAR_UNKNOWN", "OFFICIAL_CONFIRMATION_UNKNOWN")
                        if index % 5 == 0 else ()
                    ),
                ),
            )
        )

    events.extend(transition)
    events.sort(key=lambda event: (event.event_date, event.event_id))
    return tuple(events)


def _role_capacity_map(resources: Mapping[str, Any]) -> dict[str, float]:
    return {
        str(row["id"]): float(row["capacity"])
        for row in resources["resources"]
        if row["kind"] == "ROLE_CAPACITY"
    }


def _all_capacity_map(resources: Mapping[str, Any]) -> dict[str, float]:
    return {
        str(row["id"]): float(row["capacity"])
        for row in resources["resources"]
    }


def _attack_capacity(
    base: Mapping[str, float],
    *,
    day_index: int,
    mode: Mapping[str, Any],
) -> dict[str, float]:
    current = dict(base)
    for rule in mode.get("outage_rules", ()):
        every = int(rule["every_days"])
        duration = int(rule["duration_days"])
        if every <= 0 or duration <= 0:
            raise ValueError("INVALID_OUTAGE_RULE")
        phase = day_index % every
        if phase < duration:
            resource_id = str(rule["resource_id"])
            if resource_id not in current:
                raise ValueError(f"OUTAGE_UNKNOWN_RESOURCE:{resource_id}")
            current[resource_id] = (
                current[resource_id] * float(rule["multiplier"])
            )
    return current


def _case_priority(event: Any, due_date: date) -> int:
    score = FAMILY_PRIORITY.get(event.family, 20)
    if "HOME_MATCH" in getattr(event, "risk_flags", ()):
        score += 10
    if "SIMULATED_STALE_STATE" in getattr(event, "risk_flags", ()):
        score += 15
    return score


def _travel_cost(event: Any) -> float:
    if event.case_type != "away_trip_plan":
        return 0.0
    km = float(event.estimated_team_route_km or 0.0)
    return round(km * 0.75, 2)


def build_annual_cases_v0(
    events: Iterable[Any],
    resources: Mapping[str, Any],
) -> tuple[AnnualCaseV0, ...]:
    workload_map = resources["family_workload_map"]
    cases = []
    for event in events:
        arrival = date.fromisoformat(event.event_date)
        deadline_days = int(FAMILY_DEADLINE_DAYS.get(event.family, 5))
        due = arrival + timedelta(days=deadline_days)
        role_demands = tuple(
            (str(resource_id), float(amount))
            for resource_id, amount in workload_map.get(event.family, ())
        )
        asset = ASSET_DEMAND_BY_CASE.get(event.case_type)
        cases.append(
            AnnualCaseV0(
                case_id=event.event_id,
                arrival_date=arrival,
                due_date=due,
                family=event.family,
                case_type=event.case_type,
                initial_gate=event.expected_gate,
                role_demands=role_demands,
                asset_demand=asset,
                estimated_travel_cost_eur=_travel_cost(event),
                priority_score=_case_priority(event, due),
                source_event=event,
            )
        )
    return tuple(cases)


def run_one_year_soak_v0(
    *,
    events: Iterable[Any],
    resources: Mapping[str, Any],
    attack_profiles: Mapping[str, Any],
    profile_id: str,
    attack_mode: str,
) -> AnnualRunResultV0:
    if attack_profiles.get("status") != TRUTH_CLASS:
        raise ValueError("ATTACK_PROFILE_STATUS_REQUIRED")
    mode = attack_profiles["modes"].get(attack_mode)
    if mode is None:
        raise ValueError(f"UNKNOWN_ATTACK_MODE:{attack_mode}")

    start = date.fromisoformat(attack_profiles["horizon"]["start"])
    end = date.fromisoformat(attack_profiles["horizon"]["end"])
    if (end - start).days + 1 != int(attack_profiles["horizon"]["days"]):
        raise ValueError("HORIZON_DAY_COUNT_MISMATCH")

    cases = build_annual_cases_v0(events, resources)
    cases_by_day: dict[date, list[AnnualCaseV0]] = defaultdict(list)
    for case in cases:
        if start <= case.arrival_date <= end:
            cases_by_day[case.arrival_date].append(case)

    capacities = _all_capacity_map(resources)
    role_capacity_ids = set(_role_capacity_map(resources))
    pending: dict[str, dict[str, Any]] = {}
    completed: set[str] = set()
    privacy_manual: set[str] = set()
    failures: list[FailureSignalV0] = []
    emitted_failure_keys: set[tuple[str, str, str | None]] = set()
    max_backlog = 0
    max_case_age = 0
    monthly_travel: dict[str, float] = defaultdict(float)

    def emit(day, failure_type, severity, case_id=None, resource_id=None, detail=""):
        key = (failure_type, str(case_id or resource_id or detail), day.isoformat())
        if key in emitted_failure_keys:
            return
        emitted_failure_keys.add(key)
        failures.append(
            FailureSignalV0(
                day=day.isoformat(),
                failure_type=failure_type,
                severity=severity,
                case_id=case_id,
                resource_id=resource_id,
                detail=detail,
            )
        )

    for day_index, day in enumerate(_date_range(start, end)):
        day_cap = _attack_capacity(
            capacities,
            day_index=day_index,
            mode=mode,
        )
        used_role: dict[str, float] = defaultdict(float)

        arrivals = cases_by_day.get(day, [])
        asset_demand_today: dict[str, float] = defaultdict(float)
        asset_cases_today: dict[str, list[str]] = defaultdict(list)

        for case in arrivals:
            if case.initial_gate == "PRE_RUNTIME_BLOCK":
                privacy_manual.add(case.case_id)
                continue

            persistent = (
                case.initial_gate in {"HOLD", "BLOCK"}
                and (sum(ord(ch) for ch in case.case_id)
                     % int(mode["persistent_unresolved_modulo"]) == 0)
            )
            if case.initial_gate == "ALLOW":
                ready_date = case.arrival_date
            elif case.initial_gate == "HOLD":
                ready_date = (
                    None if persistent
                    else case.arrival_date
                    + timedelta(days=int(mode["hold_resolution_days"]))
                )
            else:
                ready_date = (
                    None if persistent
                    else case.arrival_date
                    + timedelta(days=int(mode["block_resolution_days"]))
                )

            pending[case.case_id] = {
                "case": case,
                "ready_date": ready_date,
                "queued_since": day,
                "deadline_miss_emitted": False,
                "starvation_emitted": False,
                "unresolved_age_emitted": False,
            }

            if case.asset_demand is not None:
                resource_id, amount = case.asset_demand
                asset_demand_today[resource_id] += float(amount)
                asset_cases_today[resource_id].append(case.case_id)

            if case.estimated_travel_cost_eur:
                monthly_travel[day.strftime("%Y-%m")] += (
                    case.estimated_travel_cost_eur
                )

        for resource_id, demand in asset_demand_today.items():
            capacity = float(day_cap.get(resource_id, 0.0))
            if demand > capacity:
                emit(
                    day,
                    "SHARED_ASSET_COLLISION",
                    "HIGH",
                    resource_id=resource_id,
                    detail=(
                        f"demand={demand:.2f};capacity={capacity:.2f};"
                        f"cases={','.join(sorted(asset_cases_today[resource_id]))}"
                    ),
                )

        travel_envelope = float(day_cap.get("TRAVEL_MONTHLY_ENVELOPE", 0.0))
        month_key = day.strftime("%Y-%m")
        if (
            travel_envelope >= 0
            and monthly_travel[month_key] > travel_envelope
        ):
            emit(
                day,
                "TRAVEL_BUDGET_PRESSURE",
                "MEDIUM",
                resource_id="TRAVEL_MONTHLY_ENVELOPE",
                detail=(
                    f"month={month_key};estimated={monthly_travel[month_key]:.2f};"
                    f"envelope={travel_envelope:.2f}"
                ),
            )

        for case_id, state in list(pending.items()):
            case = state["case"]
            age = (day - case.arrival_date).days
            max_case_age = max(max_case_age, age)

            if day > case.due_date and not state["deadline_miss_emitted"]:
                emit(
                    day,
                    "DEADLINE_MISS",
                    "HIGH",
                    case_id=case_id,
                    detail=(
                        f"family={case.family};gate={case.initial_gate};"
                        f"due={case.due_date.isoformat()}"
                    ),
                )
                state["deadline_miss_emitted"] = True

            ready_date = state["ready_date"]
            if ready_date is None:
                threshold = (
                    int(mode["hold_resolution_days"])
                    if case.initial_gate == "HOLD"
                    else int(mode["block_resolution_days"])
                )
                if age > threshold and not state["unresolved_age_emitted"]:
                    emit(
                        day,
                        (
                            "UNRESOLVED_HOLD_AGING"
                            if case.initial_gate == "HOLD"
                            else "UNRESOLVED_BLOCK_AGING"
                        ),
                        "HIGH",
                        case_id=case_id,
                        detail=f"age_days={age};persistent_simulated_unresolved=true",
                    )
                    state["unresolved_age_emitted"] = True
                continue

        ready_cases = [
            state["case"]
            for state in pending.values()
            if state["ready_date"] is not None
            and state["ready_date"] <= day
        ]
        ready_cases.sort(
            key=lambda case: (
                -case.priority_score,
                case.due_date,
                case.arrival_date,
                case.case_id,
            )
        )

        for case in ready_cases:
            state = pending.get(case.case_id)
            if state is None:
                continue

            can_process = True
            for resource_id, amount in case.role_demands:
                if resource_id not in role_capacity_ids:
                    continue
                if used_role[resource_id] + amount > float(day_cap[resource_id]):
                    can_process = False
                    break

            if can_process:
                for resource_id, amount in case.role_demands:
                    if resource_id in role_capacity_ids:
                        used_role[resource_id] += amount
                completed.add(case.case_id)
                pending.pop(case.case_id, None)
            else:
                wait_days = (day - state["ready_date"]).days
                if (
                    wait_days >= int(mode["starvation_failure_days"])
                    and not state["starvation_emitted"]
                ):
                    blocking_resources = [
                        resource_id
                        for resource_id, amount in case.role_demands
                        if resource_id in role_capacity_ids
                        and used_role[resource_id] + amount
                        > float(day_cap[resource_id])
                    ]
                    emit(
                        day,
                        "RESOURCE_STARVATION",
                        "MEDIUM",
                        case_id=case.case_id,
                        detail=(
                            f"wait_days={wait_days};"
                            f"resources={','.join(blocking_resources)}"
                        ),
                    )
                    state["starvation_emitted"] = True

        backlog = len(pending)
        max_backlog = max(max_backlog, backlog)
        if backlog > int(mode["backlog_failure_threshold"]):
            emit(
                day,
                "BACKLOG_SATURATION",
                "HIGH",
                detail=(
                    f"pending={backlog};"
                    f"threshold={mode['backlog_failure_threshold']}"
                ),
            )

    for case_id, state in pending.items():
        case = state["case"]
        emit(
            end,
            "YEAR_END_UNRESOLVED",
            "HIGH",
            case_id=case_id,
            detail=(
                f"gate={case.initial_gate};arrival={case.arrival_date.isoformat()};"
                f"due={case.due_date.isoformat()}"
            ),
        )

    return AnnualRunResultV0(
        profile_id=profile_id,
        attack_mode=attack_mode,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        day_count=(end - start).days + 1,
        input_event_count=len(cases),
        completed_case_count=len(completed),
        pending_case_count=len(pending),
        privacy_manual_review_count=len(privacy_manual),
        failure_signals=tuple(failures),
        max_backlog=max_backlog,
        max_case_age_days=max_case_age,
        monthly_travel_costs=tuple(
            sorted((month, round(value, 2)) for month, value in monthly_travel.items())
        ),
    )


def failure_summary_v0(result: AnnualRunResultV0) -> dict[str, Any]:
    by_type = Counter(signal.failure_type for signal in result.failure_signals)
    by_severity = Counter(signal.severity for signal in result.failure_signals)
    first_by_type = {}
    for signal in sorted(
        result.failure_signals,
        key=lambda row: (row.day, row.failure_type, row.case_id or ""),
    ):
        first_by_type.setdefault(signal.failure_type, signal.day)

    return {
        "status": result.status,
        "profile_id": result.profile_id,
        "attack_mode": result.attack_mode,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "day_count": result.day_count,
        "input_event_count": result.input_event_count,
        "completed_case_count": result.completed_case_count,
        "pending_case_count": result.pending_case_count,
        "privacy_manual_review_count": result.privacy_manual_review_count,
        "failure_signal_count": len(result.failure_signals),
        "failure_types": dict(sorted(by_type.items())),
        "failure_severity": dict(sorted(by_severity.items())),
        "first_failure_by_type": dict(sorted(first_by_type.items())),
        "max_backlog": result.max_backlog,
        "max_case_age_days": result.max_case_age_days,
        "external_action": False,
        "authority": "KX108_ONLY",
    }


def compare_run_matrix_v0(
    runs: Iterable[AnnualRunResultV0],
) -> dict[str, Any]:
    rows = tuple(runs)
    return {
        "status": STATUS,
        "run_count": len(rows),
        "runs": [failure_summary_v0(row) for row in rows],
        "best_by_failure_count": min(
            rows,
            key=lambda row: len(row.failure_signals),
        ).profile_id
        + "/"
        + min(rows, key=lambda row: len(row.failure_signals)).attack_mode,
        "worst_by_failure_count": max(
            rows,
            key=lambda row: len(row.failure_signals),
        ).profile_id
        + "/"
        + max(rows, key=lambda row: len(row.failure_signals)).attack_mode,
        "external_action": False,
        "authority": "KX108_ONLY",
    }
