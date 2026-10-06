"""F3B — CSSA field intake contracts V0.

Purpose:
- capture real CSSA administrative examples without guessing internal practice;
- preserve provenance, uncertainty, contradictions and authority boundaries;
- support anonymized/sample-based READONLY intake first.

This is an intake/evidence layer, not an automation layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from universal.contracts.domain_v0 import DomainStateRefV0


EVIDENCE_CLASSES = {
    "OBSERVED_DIRECTLY",
    "STAFF_STATEMENT",
    "INTERNAL_DOCUMENT",
    "SYSTEM_SCREEN_STATE",
    "EMAIL_THREAD",
    "OFFICIAL_EXTERNAL_DECISION",
    "LOCAL_CHECKLIST",
    "INFERRED_PATTERN",
}

SENSITIVITY_CLASSES = {
    "PUBLIC",
    "INTERNAL",
    "PERSONAL_DATA",
    "MINOR_DATA",
    "HEALTH_DATA",
    "DISCIPLINARY_DATA",
    "FINANCIAL_DATA",
}

HIGH_SENSITIVITY = {
    "MINOR_DATA",
    "HEALTH_DATA",
    "DISCIPLINARY_DATA",
    "FINANCIAL_DATA",
}


@dataclass(frozen=True)
class CSSAFieldSourceV0:
    source_id: str
    evidence_class: str
    observed_at: str
    source_type: str
    source_ref: str
    sensitivity: tuple[str, ...] = ("INTERNAL",)
    anonymized: bool = False
    retention_note: str = ""
    access_scope: str = "READONLY"
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(f"unknown evidence_class: {self.evidence_class}")
        unknown_sensitivity = set(self.sensitivity) - SENSITIVITY_CLASSES
        if unknown_sensitivity:
            raise ValueError(
                f"unknown sensitivity class(es): {sorted(unknown_sensitivity)}"
            )
        if self.access_scope != "READONLY":
            raise ValueError("F3B intake source must remain READONLY")

    @property
    def requires_manual_privacy_review(self) -> bool:
        return bool(set(self.sensitivity) & HIGH_SENSITIVITY)

    @property
    def runtime_ingest_allowed(self) -> bool:
        # High-sensitivity material is stopped at the intake boundary in V0.
        return not self.requires_manual_privacy_review


@dataclass(frozen=True)
class CSSAFieldCaseV0:
    case_ref: str
    case_type_observed: str
    valid_at: str
    source_ids: tuple[str, ...]
    trigger: str = ""
    target_refs: tuple[str, ...] = ()
    responsible_role_observed: str | None = None
    approving_role_observed: str | None = None
    external_authority_observed: str | None = None
    deadline_observed: str | None = None
    channel_observed: str | None = None
    tools_observed: tuple[str, ...] = ()
    required_documents_observed: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    exceptions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    result_observed: str | None = None
    proof_refs: tuple[str, ...] = ()
    human_memory_only_refs: tuple[str, ...] = ()
    local_practice_refs: tuple[str, ...] = ()
    public_rule_refs: tuple[str, ...] = ()
    validated_by_cssa: bool = False
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    decision_authority: str = "KX108_ONLY"

    def __post_init__(self) -> None:
        if not self.case_ref:
            raise ValueError("case_ref is required")
        if not self.case_type_observed:
            raise ValueError("case_type_observed is required")
        if not self.valid_at:
            raise ValueError("valid_at is required")
        if not self.source_ids:
            raise ValueError("at least one source_id is required")
        if self.decision_authority != "KX108_ONLY":
            raise ValueError("decision authority must remain KX108_ONLY")
        if self.allowed_to_decide:
            raise ValueError("field case cannot decide")
        if self.allowed_to_act:
            raise ValueError("field case cannot act")

    def to_domain_state_ref(self) -> DomainStateRefV0:
        unknowns = list(self.missing_information)
        if not self.validated_by_cssa:
            unknowns.append("FIELD_CASE_NOT_YET_CSSA_VALIDATED")

        risk_flags = list(self.risk_flags)
        if self.human_memory_only_refs:
            risk_flags.append("HUMAN_MEMORY_ONLY_DEPENDENCY")
        if self.exceptions:
            risk_flags.append("EXCEPTION_PATH_OBSERVED")

        evidence_refs = tuple(
            dict.fromkeys(
                [
                    *self.source_ids,
                    *self.proof_refs,
                    *self.public_rule_refs,
                    *self.local_practice_refs,
                ]
            )
        )

        return DomainStateRefV0(
            domain_id="administration",
            state_ref=f"cssa-field:{self.case_ref}",
            valid_at=self.valid_at,
            upstream_state_ref=f"cssa-field-sources:{self.case_ref}",
            unknowns=tuple(sorted(set(unknowns))),
            contradictions=tuple(sorted(set(self.contradictions))),
            risk_flags=tuple(sorted(set(risk_flags))),
            evidence_refs=evidence_refs,
            provenance_refs=self.source_ids,
        )

    def to_runtime_mapping(self, *, confidence: float) -> dict[str, Any]:
        state = self.to_domain_state_ref()
        return {
            "case_ref": state.state_ref,
            "valid_at": state.valid_at,
            "source_ref": state.upstream_state_ref,
            "unknowns": state.unknowns,
            "contradictions": state.contradictions,
            "risk_flags": state.risk_flags,
            "evidence_refs": state.evidence_refs,
            "provenance_refs": state.provenance_refs,
            "confidence": float(confidence),
            # CSSA-only observed semantics stop at the adapter boundary.
            "case_type_observed": self.case_type_observed,
            "responsible_role_observed": self.responsible_role_observed,
            "approving_role_observed": self.approving_role_observed,
            "external_authority_observed": self.external_authority_observed,
            "deadline_observed": self.deadline_observed,
            "channel_observed": self.channel_observed,
            "tools_observed": self.tools_observed,
            "validated_by_cssa": self.validated_by_cssa,
        }


@dataclass(frozen=True)
class CSSAFieldBundleV0:
    sources: tuple[CSSAFieldSourceV0, ...]
    cases: tuple[CSSAFieldCaseV0, ...]
    bundle_ref: str = "cssa-field-bundle-v0"

    def source_index(self) -> dict[str, CSSAFieldSourceV0]:
        return {source.source_id: source for source in self.sources}

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        index = self.source_index()

        if len(index) != len(self.sources):
            errors.append("DUPLICATE_SOURCE_ID")

        case_refs: set[str] = set()
        for case in self.cases:
            if case.case_ref in case_refs:
                errors.append(f"DUPLICATE_CASE_REF:{case.case_ref}")
            case_refs.add(case.case_ref)

            for source_id in case.source_ids:
                if source_id not in index:
                    errors.append(
                        f"MISSING_SOURCE_REF:{case.case_ref}:{source_id}"
                    )

        return tuple(errors)

    def runtime_ready_case_refs(self) -> tuple[str, ...]:
        index = self.source_index()
        ready: list[str] = []
        for case in self.cases:
            if all(index[sid].runtime_ingest_allowed for sid in case.source_ids):
                ready.append(case.case_ref)
        return tuple(ready)
