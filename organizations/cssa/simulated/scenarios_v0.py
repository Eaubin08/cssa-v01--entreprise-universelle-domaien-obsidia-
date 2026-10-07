"""F3C — simulated CSSA field scenarios V0.

These scenarios are intentionally synthetic.

They are shaped by:
- current public FFF/LGEF rules already frozen in F3A;
- sanitized patterns visible in CSSA supporter communications;
- the F3B field-intake contract.

They are NOT claims about CSSA internal procedures.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from organizations.cssa.field.contracts_v0 import (
    CSSAFieldBundleV0,
    CSSAFieldCaseV0,
    CSSAFieldSourceV0,
)


SIMULATION_STATUS = "SIMULATED_NOT_OBSERVED"


@dataclass(frozen=True)
class CSSASimulatedScenarioV0:
    scenario_id: str
    title: str
    family: str
    description: str
    source_patterns: tuple[str, ...]
    public_rule_refs: tuple[str, ...]
    field_case: CSSAFieldCaseV0
    expected_gate: str
    expected_provider_invoked: bool
    simulation_status: str = SIMULATION_STATUS

    def __post_init__(self) -> None:
        if self.simulation_status != SIMULATION_STATUS:
            raise ValueError("F3C scenarios must remain explicitly simulated")
        if self.expected_gate not in {"ALLOW", "HOLD", "BLOCK", "PRE_RUNTIME_BLOCK"}:
            raise ValueError(f"unexpected gate: {self.expected_gate}")

    def to_bundle(self) -> CSSAFieldBundleV0:
        sources = tuple(
            CSSAFieldSourceV0(
                source_id=source_id,
                evidence_class="INFERRED_PATTERN",
                observed_at=self.field_case.valid_at,
                source_type="SIMULATED_SCENARIO_SOURCE",
                source_ref=source_id,
                sensitivity=("PUBLIC",),
                anonymized=True,
                access_scope="READONLY",
                provenance_refs=("F3C_SIMULATION_ONLY",),
            )
            for source_id in self.field_case.source_ids
        )
        return CSSAFieldBundleV0(
            sources=sources,
            cases=(self.field_case,),
            bundle_ref=f"simulated:{self.scenario_id}",
        )


def scenario_from_mapping(raw: Mapping[str, Any]) -> CSSASimulatedScenarioV0:
    case = CSSAFieldCaseV0(
        case_ref=str(raw["case_ref"]),
        case_type_observed=str(raw["case_type_observed"]),
        valid_at=str(raw["valid_at"]),
        source_ids=tuple(str(v) for v in raw["source_ids"]),
        trigger=str(raw.get("trigger", "")),
        target_refs=tuple(str(v) for v in raw.get("target_refs", ())),
        responsible_role_observed=raw.get("responsible_role_observed"),
        approving_role_observed=raw.get("approving_role_observed"),
        external_authority_observed=raw.get("external_authority_observed"),
        deadline_observed=raw.get("deadline_observed"),
        channel_observed=raw.get("channel_observed"),
        tools_observed=tuple(str(v) for v in raw.get("tools_observed", ())),
        required_documents_observed=tuple(
            str(v) for v in raw.get("required_documents_observed", ())
        ),
        missing_information=tuple(
            str(v) for v in raw.get("missing_information", ())
        ),
        contradictions=tuple(str(v) for v in raw.get("contradictions", ())),
        exceptions=tuple(str(v) for v in raw.get("exceptions", ())),
        risk_flags=tuple(str(v) for v in raw.get("risk_flags", ())),
        result_observed=raw.get("result_observed"),
        proof_refs=tuple(str(v) for v in raw.get("proof_refs", ())),
        human_memory_only_refs=tuple(
            str(v) for v in raw.get("human_memory_only_refs", ())
        ),
        local_practice_refs=tuple(
            str(v) for v in raw.get("local_practice_refs", ())
        ),
        public_rule_refs=tuple(str(v) for v in raw.get("public_rule_refs", ())),
        validated_by_cssa=bool(raw.get("validated_by_cssa", True)),
    )
    return CSSASimulatedScenarioV0(
        scenario_id=str(raw["scenario_id"]),
        title=str(raw["title"]),
        family=str(raw["family"]),
        description=str(raw["description"]),
        source_patterns=tuple(str(v) for v in raw.get("source_patterns", ())),
        public_rule_refs=tuple(str(v) for v in raw.get("public_rule_refs", ())),
        field_case=case,
        expected_gate=str(raw["expected_gate"]),
        expected_provider_invoked=bool(raw["expected_provider_invoked"]),
        simulation_status=str(raw.get("simulation_status", SIMULATION_STATUS)),
    )
