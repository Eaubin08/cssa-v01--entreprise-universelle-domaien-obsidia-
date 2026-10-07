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
    source_sensitivity: tuple[str, ...] = ("PUBLIC",)
    simulation_truth_assumed: bool = True
    simulation_status: str = SIMULATION_STATUS

    def __post_init__(self) -> None:
        if self.simulation_status != SIMULATION_STATUS:
            raise ValueError("F3C scenarios must remain explicitly simulated")
        if self.expected_gate not in {"ALLOW", "HOLD", "BLOCK", "PRE_RUNTIME_BLOCK"}:
            raise ValueError(f"unexpected gate: {self.expected_gate}")

    def to_simulated_runtime_mapping(self, *, confidence: float) -> dict[str, Any]:
        """Build a runtime mapping using scenario truth, not CSSA validation.

        This method is F3C-only. It deliberately does NOT set
        validated_by_cssa=True. The scenario remains SIMULATED_NOT_OBSERVED.
        """
        unknowns = list(self.field_case.missing_information)
        risk_flags = list(self.field_case.risk_flags)
        if self.field_case.human_memory_only_refs:
            risk_flags.append("HUMAN_MEMORY_ONLY_DEPENDENCY")
        if self.field_case.exceptions:
            risk_flags.append("EXCEPTION_PATH_OBSERVED")

        evidence_refs = tuple(
            dict.fromkeys(
                [
                    *self.field_case.source_ids,
                    *self.field_case.proof_refs,
                    *self.field_case.public_rule_refs,
                    *self.field_case.local_practice_refs,
                ]
            )
        )

        return {
            "case_ref": f"cssa-simulated:{self.field_case.case_ref}",
            "valid_at": self.field_case.valid_at,
            "source_ref": f"cssa-simulated-sources:{self.field_case.case_ref}",
            "unknowns": tuple(sorted(set(unknowns))),
            "contradictions": tuple(
                sorted(set(self.field_case.contradictions))
            ),
            "risk_flags": tuple(sorted(set(risk_flags))),
            "evidence_refs": evidence_refs,
            "provenance_refs": self.field_case.source_ids,
            "confidence": float(confidence),
            "simulation_status": self.simulation_status,
            "simulation_truth_assumed": self.simulation_truth_assumed,
            "scenario_id": self.scenario_id,
        }

    def to_bundle(self) -> CSSAFieldBundleV0:
        sources = tuple(
            CSSAFieldSourceV0(
                source_id=source_id,
                evidence_class="INFERRED_PATTERN",
                observed_at=self.field_case.valid_at,
                source_type="SIMULATED_SCENARIO_SOURCE",
                source_ref=source_id,
                sensitivity=self.source_sensitivity,
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
        # Never claim real CSSA validation for a synthetic scenario.
        validated_by_cssa=False,
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
        source_sensitivity=tuple(
            str(v) for v in raw.get("source_sensitivity", ("PUBLIC",))
        ),
        simulation_truth_assumed=bool(
            raw.get("simulation_truth_assumed", True)
        ),
        simulation_status=str(raw.get("simulation_status", SIMULATION_STATUS)),
    )
