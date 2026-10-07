"""F3G-F — coverage of the CSSA publicly announced Manager Général role.

This layer treats the official job description as a public business contract to
test against the current CSSA model. It does not infer private operations and it
does not enable any external action.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

ALLOWED_LEVELS = {"STRUCTURALLY_COVERED", "PARTIAL", "OPEN_GAP"}
ALLOWED_FUTURE_SURFACES = {"MAIL", "CALENDAR", "CRM", "TASKS"}
STATUS = "PUBLIC_ANNOUNCED_ROLE_CONTRACT_READONLY"


def validate_announced_role_coverage_v0(
    model: Mapping[str, Any],
) -> None:
    if model.get("status") != STATUS:
        raise ValueError("INVALID_ANNOUNCED_ROLE_COVERAGE_STATUS")

    source = model.get("source", {})
    if source.get("truth_class") != "PUBLIC_CONFIRMED":
        raise ValueError("ANNOUNCED_ROLE_SOURCE_MUST_BE_PUBLIC_CONFIRMED")
    if not str(source.get("url", "")).startswith("https://"):
        raise ValueError("ANNOUNCED_ROLE_SOURCE_MUST_BE_HTTPS")

    boundary = model.get("global_boundaries", {})
    if boundary.get("real_field_evidence") is not False:
        raise ValueError("ANNOUNCED_ROLE_IS_NOT_REAL_FIELD_EVIDENCE")
    if boundary.get("external_action") is not False:
        raise ValueError("ANNOUNCED_ROLE_COVERAGE_MUST_BE_READONLY")
    if boundary.get("decision_authority") != "KX108_ONLY":
        raise ValueError("DECISION_AUTHORITY_MUST_REMAIN_KX108_ONLY")
    if boundary.get("memory_write") is not False:
        raise ValueError("MEMORY_WRITE_MUST_REMAIN_FALSE")
    if boundary.get("emits_act") is not False:
        raise ValueError("EMITS_ACT_MUST_REMAIN_FALSE")
    if boundary.get("kernel_mutation") is not False:
        raise ValueError("KERNEL_MUTATION_MUST_REMAIN_FALSE")

    seen: set[str] = set()
    for row in model.get("requirements", ()):
        req_id = str(row.get("id", "")).strip()
        if not req_id:
            raise ValueError("ANNOUNCED_REQUIREMENT_ID_REQUIRED")
        if req_id in seen:
            raise ValueError(f"DUPLICATE_ANNOUNCED_REQUIREMENT:{req_id}")
        seen.add(req_id)

        level = str(row.get("coverage_level", ""))
        if level not in ALLOWED_LEVELS:
            raise ValueError(f"INVALID_COVERAGE_LEVEL:{req_id}:{level}")

        if not row.get("announced_scope"):
            raise ValueError(f"ANNOUNCED_SCOPE_REQUIRED:{req_id}")
        if not row.get("families"):
            raise ValueError(f"ANNOUNCED_FAMILY_REQUIRED:{req_id}")
        if not row.get("proof_refs"):
            raise ValueError(f"PROOF_REF_REQUIRED:{req_id}")

        surfaces = {str(v) for v in row.get("future_surfaces", ())}
        invalid = sorted(surfaces - ALLOWED_FUTURE_SURFACES)
        if invalid:
            raise ValueError(
                f"INVALID_FUTURE_SURFACE:{req_id}:{','.join(invalid)}"
            )

        # Even structurally covered requirements are not operationally proven
        # against the real internal CSSA organization at this stage.
        if row.get("field_proven") is True:
            raise ValueError(f"FALSE_FIELD_PROOF_FORBIDDEN:{req_id}")


def coverage_summary_v0(
    model: Mapping[str, Any],
) -> dict[str, Any]:
    validate_announced_role_coverage_v0(model)
    rows = tuple(model["requirements"])
    levels = Counter(str(row["coverage_level"]) for row in rows)
    future_surfaces = Counter(
        surface
        for row in rows
        for surface in row.get("future_surfaces", ())
    )
    gaps = [
        str(row["id"])
        for row in rows
        if row["coverage_level"] == "OPEN_GAP"
    ]
    partial = [
        str(row["id"])
        for row in rows
        if row["coverage_level"] == "PARTIAL"
    ]
    return {
        "status": STATUS,
        "requirement_count": len(rows),
        "coverage_counts": dict(sorted(levels.items())),
        "open_gap_ids": gaps,
        "partial_ids": partial,
        "future_surface_demand": dict(sorted(future_surfaces.items())),
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }


def operationalization_queue_v0(
    model: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Return next-action candidates without enabling them.

    OPEN_GAP is ranked before PARTIAL, then STRUCTURALLY_COVERED. Within the
    same level, requirements touching more future action surfaces rank first.
    """
    validate_announced_role_coverage_v0(model)
    rank = {
        "OPEN_GAP": 0,
        "PARTIAL": 1,
        "STRUCTURALLY_COVERED": 2,
    }
    rows = []
    for row in model["requirements"]:
        rows.append({
            "requirement_id": str(row["id"]),
            "coverage_level": str(row["coverage_level"]),
            "open_gaps": tuple(str(v) for v in row.get("open_gaps", ())),
            "future_surfaces": tuple(
                str(v) for v in row.get("future_surfaces", ())
            ),
            "external_action_enabled": False,
        })
    rows.sort(
        key=lambda row: (
            rank[row["coverage_level"]],
            -len(row["future_surfaces"]),
            row["requirement_id"],
        )
    )
    return tuple(rows)


def manager_route_coverage_v0(
    model: Mapping[str, Any],
    routing: Mapping[str, Any],
) -> dict[str, Any]:
    """Check whether announced families are visible to MANAGER_GENERAL."""
    validate_announced_role_coverage_v0(model)
    required_families = sorted({
        family
        for row in model["requirements"]
        for family in row["families"]
        if family in routing["family_routes"]
    })
    missing = [
        family
        for family in required_families
        if "MANAGER_GENERAL" not in routing["family_routes"][family]
    ]
    return {
        "required_family_count": len(required_families),
        "required_families": required_families,
        "missing_manager_routes": missing,
        "complete": not missing,
    }


def proof_ref_set_v0(
    model: Mapping[str, Any],
) -> tuple[str, ...]:
    validate_announced_role_coverage_v0(model)
    return tuple(sorted({
        str(ref)
        for row in model["requirements"]
        for ref in row["proof_refs"]
    }))


def action_surface_requirements_v0(
    model: Mapping[str, Any],
    surface: str,
) -> tuple[str, ...]:
    validate_announced_role_coverage_v0(model)
    if surface not in ALLOWED_FUTURE_SURFACES:
        raise ValueError(f"UNKNOWN_ACTION_SURFACE:{surface}")
    return tuple(
        str(row["id"])
        for row in model["requirements"]
        if surface in row.get("future_surfaces", ())
    )
