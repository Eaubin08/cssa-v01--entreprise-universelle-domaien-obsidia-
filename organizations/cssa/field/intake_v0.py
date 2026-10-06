"""F3B — safe mapping from field forms/dicts into typed CSSA intake contracts."""
from __future__ import annotations

from typing import Any, Mapping

from .contracts_v0 import CSSAFieldBundleV0, CSSAFieldCaseV0, CSSAFieldSourceV0


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(v) for v in value)
    if isinstance(value, list):
        return tuple(str(v) for v in value)
    if isinstance(value, str):
        return (value,) if value else ()
    raise ValueError("expected string/list/tuple")


def source_from_mapping(raw: Mapping[str, Any]) -> CSSAFieldSourceV0:
    return CSSAFieldSourceV0(
        source_id=str(raw["source_id"]),
        evidence_class=str(raw["evidence_class"]),
        observed_at=str(raw["observed_at"]),
        source_type=str(raw.get("source_type", "UNKNOWN")),
        source_ref=str(raw.get("source_ref", raw["source_id"])),
        sensitivity=_tuple(raw.get("sensitivity", ("INTERNAL",))),
        anonymized=bool(raw.get("anonymized", False)),
        retention_note=str(raw.get("retention_note", "")),
        access_scope=str(raw.get("access_scope", "READONLY")),
        provenance_refs=_tuple(raw.get("provenance_refs")),
    )


def case_from_mapping(raw: Mapping[str, Any]) -> CSSAFieldCaseV0:
    return CSSAFieldCaseV0(
        case_ref=str(raw["case_ref"]),
        case_type_observed=str(raw["case_type_observed"]),
        valid_at=str(raw["valid_at"]),
        source_ids=_tuple(raw["source_ids"]),
        trigger=str(raw.get("trigger", "")),
        target_refs=_tuple(raw.get("target_refs")),
        responsible_role_observed=raw.get("responsible_role_observed"),
        approving_role_observed=raw.get("approving_role_observed"),
        external_authority_observed=raw.get("external_authority_observed"),
        deadline_observed=raw.get("deadline_observed"),
        channel_observed=raw.get("channel_observed"),
        tools_observed=_tuple(raw.get("tools_observed")),
        required_documents_observed=_tuple(
            raw.get("required_documents_observed")
        ),
        missing_information=_tuple(raw.get("missing_information")),
        contradictions=_tuple(raw.get("contradictions")),
        exceptions=_tuple(raw.get("exceptions")),
        risk_flags=_tuple(raw.get("risk_flags")),
        result_observed=raw.get("result_observed"),
        proof_refs=_tuple(raw.get("proof_refs")),
        human_memory_only_refs=_tuple(raw.get("human_memory_only_refs")),
        local_practice_refs=_tuple(raw.get("local_practice_refs")),
        public_rule_refs=_tuple(raw.get("public_rule_refs")),
        validated_by_cssa=bool(raw.get("validated_by_cssa", False)),
    )


def bundle_from_mapping(raw: Mapping[str, Any]) -> CSSAFieldBundleV0:
    bundle = CSSAFieldBundleV0(
        sources=tuple(source_from_mapping(x) for x in raw.get("sources", ())),
        cases=tuple(case_from_mapping(x) for x in raw.get("cases", ())),
        bundle_ref=str(raw.get("bundle_ref", "cssa-field-bundle-v0")),
    )
    errors = bundle.validate()
    if errors:
        raise ValueError(";".join(errors))
    return bundle
