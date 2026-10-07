"""F3H-F — CSSA operational source registry V0.

The registry answers one question before F3H-E intake:
"Is this exact external source an explicitly authorized READONLY operational
source for CSSA?"

It does not grant decision authority, execution authority or write access.

Supported source kinds:
- MAILBOX
- DOCUMENT_REPOSITORY
- CALENDAR
- FORM_INBOX
- API_READONLY

All registered capabilities must be read-only. Write/send/delete/update
capabilities are structurally forbidden in this phase.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from organizations.cssa.intake.readonly_router_v0 import (
    DECISION_AUTHORITY,
    ReadonlySourceAuthorityV0,
    SOURCE_CSSA_OPERATIONAL_MAILBOX,
    build_readonly_source_authority_v0,
)

STATUS = "CSSA_OPERATIONAL_SOURCE_REGISTRY_V0"

SOURCE_MAILBOX = "MAILBOX"
SOURCE_DOCUMENT_REPOSITORY = "DOCUMENT_REPOSITORY"
SOURCE_CALENDAR = "CALENDAR"
SOURCE_FORM_INBOX = "FORM_INBOX"
SOURCE_API_READONLY = "API_READONLY"

SOURCE_KINDS = {
    SOURCE_MAILBOX,
    SOURCE_DOCUMENT_REPOSITORY,
    SOURCE_CALENDAR,
    SOURCE_FORM_INBOX,
    SOURCE_API_READONLY,
}

READONLY_CAPABILITIES = {
    "LIST",
    "SEARCH",
    "READ_MESSAGE",
    "READ_THREAD",
    "READ_ATTACHMENT",
    "READ_DOCUMENT",
    "READ_FILE_METADATA",
    "READ_EVENT",
    "READ_FORM_RESPONSE",
    "READ_API_RESOURCE",
}

WRITE_LIKE_FRAGMENTS = (
    "WRITE",
    "SEND",
    "CREATE",
    "UPDATE",
    "DELETE",
    "TRASH",
    "ARCHIVE",
    "MOVE",
    "REPLY",
    "FORWARD",
    "UPLOAD",
    "MUTATE",
    "EXECUTE",
)

_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,180}$")


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _require_time(value: str) -> str:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("SOURCE_REGISTRY_TIME_MUST_BE_TIMEZONE_AWARE")
    return value


@dataclass(frozen=True)
class OperationalSourceRegistrationV0:
    schema: str
    source_id: str
    source_kind: str
    provider: str
    source_identity_sha256: str
    capabilities: tuple[str, ...]
    authority_reference: str
    approved_by: str
    registered_at: str
    active: bool
    readonly: bool
    internal_cssa_source: bool
    external_mutation_allowed: bool
    is_execution_authority: bool
    decision_authority: str
    registration_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = list(self.capabilities)
        return data


@dataclass(frozen=True)
class OperationalSourceRevocationV0:
    schema: str
    revocation_id: str
    source_id: str
    registration_hash: str
    reason: str
    revoked_by: str
    revoked_at: str
    is_execution_authority: bool
    decision_authority: str
    revocation_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReadonlySourceItemV0:
    schema: str
    item_id: str
    source_id: str
    source_kind: str
    provider: str
    registration_hash: str
    provider_item_id_sha256: str
    content_sha256: str
    metadata_sha256: str
    observed_at: str
    raw_provider_item_id_persisted: bool
    raw_content_persisted: bool
    raw_source_identity_persisted: bool
    allowed_to_decide: bool
    allowed_to_act: bool
    decision_authority: str
    item_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _registration_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "source_id",
        "source_kind",
        "provider",
        "source_identity_sha256",
        "capabilities",
        "authority_reference",
        "approved_by",
        "registered_at",
        "active",
        "readonly",
        "internal_cssa_source",
        "external_mutation_allowed",
        "is_execution_authority",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_operational_source_registration_v0(
    *,
    source_id: str,
    source_kind: str,
    provider: str,
    source_identity_sha256: str,
    capabilities: tuple[str, ...],
    authority_reference: str,
    approved_by: str,
    registered_at: str,
) -> OperationalSourceRegistrationV0:
    if not _ID_RE.match(source_id):
        raise ValueError("SOURCE_REGISTRY_SOURCE_ID_INVALID")
    if source_kind not in SOURCE_KINDS:
        raise ValueError("SOURCE_REGISTRY_KIND_INVALID")
    if not provider or not authority_reference:
        raise ValueError("SOURCE_REGISTRY_PROVIDER_AUTHORITY_REQUIRED")
    if approved_by == "MACHINE" or not approved_by:
        raise ValueError("SOURCE_REGISTRY_HUMAN_APPROVER_REQUIRED")
    if len(source_identity_sha256) != 64:
        raise ValueError("SOURCE_REGISTRY_IDENTITY_HASH_INVALID")
    _require_time(registered_at)
    if not capabilities:
        raise ValueError("SOURCE_REGISTRY_CAPABILITIES_REQUIRED")

    normalized = tuple(sorted(set(str(cap) for cap in capabilities)))
    for capability in normalized:
        upper = capability.upper()
        if any(fragment in upper for fragment in WRITE_LIKE_FRAGMENTS):
            raise ValueError(
                f"SOURCE_REGISTRY_WRITE_CAPABILITY_FORBIDDEN:{capability}"
            )
        if capability not in READONLY_CAPABILITIES:
            raise ValueError(
                f"SOURCE_REGISTRY_CAPABILITY_UNSUPPORTED:{capability}"
            )

    payload = {
        "schema": "CSSA_OPERATIONAL_SOURCE_REGISTRATION_V0",
        "source_id": source_id,
        "source_kind": source_kind,
        "provider": provider,
        "source_identity_sha256": source_identity_sha256,
        "capabilities": list(normalized),
        "authority_reference": authority_reference,
        "approved_by": approved_by,
        "registered_at": registered_at,
        "active": True,
        "readonly": True,
        "internal_cssa_source": True,
        "external_mutation_allowed": False,
        "is_execution_authority": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    return OperationalSourceRegistrationV0(
        schema=payload["schema"],
        source_id=source_id,
        source_kind=source_kind,
        provider=provider,
        source_identity_sha256=source_identity_sha256,
        capabilities=normalized,
        authority_reference=authority_reference,
        approved_by=approved_by,
        registered_at=registered_at,
        active=True,
        readonly=True,
        internal_cssa_source=True,
        external_mutation_allowed=False,
        is_execution_authority=False,
        decision_authority=DECISION_AUTHORITY,
        registration_hash=_hash(payload),
    )


def verify_operational_source_registration_v0(
    registration: OperationalSourceRegistrationV0 | Mapping[str, Any] | None,
) -> tuple[bool, Optional[str]]:
    if registration is None:
        return False, "SOURCE_REGISTRY_REGISTRATION_MISSING"
    data = (
        registration.to_dict()
        if isinstance(registration, OperationalSourceRegistrationV0)
        else dict(registration)
    )
    if data.get("schema") != "CSSA_OPERATIONAL_SOURCE_REGISTRATION_V0":
        return False, "SOURCE_REGISTRY_SCHEMA_INVALID"
    if data.get("source_kind") not in SOURCE_KINDS:
        return False, "SOURCE_REGISTRY_KIND_INVALID"
    if not _ID_RE.match(str(data.get("source_id", ""))):
        return False, "SOURCE_REGISTRY_SOURCE_ID_INVALID"
    if len(str(data.get("source_identity_sha256", ""))) != 64:
        return False, "SOURCE_REGISTRY_IDENTITY_HASH_INVALID"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_REGISTRY_DECISION_AUTHORITY_INVALID"
    if data.get("active") is not True:
        return False, "SOURCE_REGISTRY_INACTIVE"
    if data.get("readonly") is not True:
        return False, "SOURCE_REGISTRY_READONLY_REQUIRED"
    if data.get("internal_cssa_source") is not True:
        return False, "SOURCE_REGISTRY_INTERNAL_SCOPE_REQUIRED"
    if data.get("external_mutation_allowed") is not False:
        return False, "SOURCE_REGISTRY_EXTERNAL_MUTATION_FORBIDDEN"
    if data.get("is_execution_authority") is not False:
        return False, "SOURCE_REGISTRY_EXECUTION_AUTHORITY_FORBIDDEN"
    capabilities = tuple(data.get("capabilities") or ())
    if not capabilities:
        return False, "SOURCE_REGISTRY_CAPABILITIES_REQUIRED"
    for capability in capabilities:
        upper = str(capability).upper()
        if any(fragment in upper for fragment in WRITE_LIKE_FRAGMENTS):
            return False, "SOURCE_REGISTRY_WRITE_CAPABILITY_FORBIDDEN"
        if capability not in READONLY_CAPABILITIES:
            return False, "SOURCE_REGISTRY_CAPABILITY_UNSUPPORTED"
    try:
        _require_time(str(data.get("registered_at")))
    except Exception:
        return False, "SOURCE_REGISTRY_REGISTERED_AT_INVALID"
    if _hash(_registration_payload(data)) != data.get("registration_hash"):
        return False, "SOURCE_REGISTRY_HASH_MISMATCH"
    return True, None


def _revocation_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "revocation_id",
        "source_id",
        "registration_hash",
        "reason",
        "revoked_by",
        "revoked_at",
        "is_execution_authority",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_source_revocation_v0(
    *,
    registration: OperationalSourceRegistrationV0,
    revocation_id: str,
    reason: str,
    revoked_by: str,
    revoked_at: str,
) -> OperationalSourceRevocationV0:
    ok, verify_reason = verify_operational_source_registration_v0(registration)
    if not ok:
        raise ValueError(verify_reason)
    if not _ID_RE.match(revocation_id):
        raise ValueError("SOURCE_REGISTRY_REVOCATION_ID_INVALID")
    if revoked_by == "MACHINE" or not revoked_by:
        raise ValueError("SOURCE_REGISTRY_REVOCATION_HUMAN_REQUIRED")
    if not reason.strip():
        raise ValueError("SOURCE_REGISTRY_REVOCATION_REASON_REQUIRED")
    _require_time(revoked_at)
    payload = {
        "schema": "CSSA_OPERATIONAL_SOURCE_REVOCATION_V0",
        "revocation_id": revocation_id,
        "source_id": registration.source_id,
        "registration_hash": registration.registration_hash,
        "reason": reason,
        "revoked_by": revoked_by,
        "revoked_at": revoked_at,
        "is_execution_authority": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    return OperationalSourceRevocationV0(
        **payload,
        revocation_hash=_hash(payload),
    )


def verify_source_revocation_v0(
    revocation: OperationalSourceRevocationV0 | Mapping[str, Any] | None,
    *,
    registration: OperationalSourceRegistrationV0,
) -> tuple[bool, Optional[str]]:
    if revocation is None:
        return False, "SOURCE_REGISTRY_REVOCATION_MISSING"
    data = (
        revocation.to_dict()
        if isinstance(revocation, OperationalSourceRevocationV0)
        else dict(revocation)
    )
    if data.get("schema") != "CSSA_OPERATIONAL_SOURCE_REVOCATION_V0":
        return False, "SOURCE_REGISTRY_REVOCATION_SCHEMA_INVALID"
    if data.get("source_id") != registration.source_id:
        return False, "SOURCE_REGISTRY_REVOCATION_SOURCE_MISMATCH"
    if data.get("registration_hash") != registration.registration_hash:
        return False, "SOURCE_REGISTRY_REVOCATION_REGISTRATION_MISMATCH"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_REGISTRY_REVOCATION_AUTHORITY_INVALID"
    if data.get("is_execution_authority") is not False:
        return False, "SOURCE_REGISTRY_REVOCATION_EXECUTION_AUTHORITY_FORBIDDEN"
    if _hash(_revocation_payload(data)) != data.get("revocation_hash"):
        return False, "SOURCE_REGISTRY_REVOCATION_HASH_MISMATCH"
    return True, None


class OperationalSourceRegistryV0:
    """File-backed source registrations with append-only revocation overlays."""

    def __init__(self, root: Path):
        self.root = root

    def _registration_path(self, source_id: str) -> Path:
        if not _ID_RE.match(source_id):
            raise ValueError("SOURCE_REGISTRY_SOURCE_ID_INVALID")
        return self.root / "registrations" / f"{source_id}.json"

    def _revocation_dir(self, source_id: str) -> Path:
        if not _ID_RE.match(source_id):
            raise ValueError("SOURCE_REGISTRY_SOURCE_ID_INVALID")
        return self.root / "revocations" / source_id

    def register(
        self,
        registration: OperationalSourceRegistrationV0,
    ) -> OperationalSourceRegistrationV0:
        ok, reason = verify_operational_source_registration_v0(registration)
        if not ok:
            raise ValueError(reason)
        path = self._registration_path(registration.source_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != registration.to_dict():
                raise ValueError("SOURCE_REGISTRY_IMMUTABLE_REGISTRATION_CONFLICT")
            return registration
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(
            json.dumps(registration.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return registration

    def load(
        self,
        source_id: str,
    ) -> Optional[OperationalSourceRegistrationV0]:
        path = self._registration_path(source_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        registration = OperationalSourceRegistrationV0(
            **{
                **data,
                "capabilities": tuple(data["capabilities"]),
            }
        )
        ok, reason = verify_operational_source_registration_v0(registration)
        if not ok:
            raise ValueError(f"SOURCE_REGISTRY_CORRUPT:{reason}")
        return registration

    def revocations(
        self,
        source_id: str,
    ) -> list[OperationalSourceRevocationV0]:
        registration = self.load(source_id)
        if registration is None:
            return []
        directory = self._revocation_dir(source_id)
        if not directory.exists():
            return []
        out: list[OperationalSourceRevocationV0] = []
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            revocation = OperationalSourceRevocationV0(**data)
            ok, reason = verify_source_revocation_v0(
                revocation,
                registration=registration,
            )
            if not ok:
                raise ValueError(f"SOURCE_REGISTRY_REVOCATION_CORRUPT:{reason}")
            out.append(revocation)
        return out

    def is_active(self, source_id: str) -> bool:
        registration = self.load(source_id)
        if registration is None:
            return False
        return len(self.revocations(source_id)) == 0

    def revoke(
        self,
        revocation: OperationalSourceRevocationV0,
    ) -> OperationalSourceRevocationV0:
        registration = self.load(revocation.source_id)
        if registration is None:
            raise ValueError("SOURCE_REGISTRY_SOURCE_NOT_FOUND")
        ok, reason = verify_source_revocation_v0(
            revocation,
            registration=registration,
        )
        if not ok:
            raise ValueError(reason)
        directory = self._revocation_dir(revocation.source_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{revocation.revocation_id}.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != revocation.to_dict():
                raise ValueError("SOURCE_REGISTRY_REVOCATION_IMMUTABILITY_CONFLICT")
            return revocation
        path.write_text(
            json.dumps(revocation.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return revocation


def mailbox_registration_to_f3h_e_authority_v0(
    *,
    registration: OperationalSourceRegistrationV0,
    registry: OperationalSourceRegistryV0,
) -> ReadonlySourceAuthorityV0:
    ok, reason = verify_operational_source_registration_v0(registration)
    if not ok:
        raise ValueError(reason)
    if registration.source_kind != SOURCE_MAILBOX:
        raise ValueError("SOURCE_REGISTRY_NOT_MAILBOX")
    if not registry.is_active(registration.source_id):
        raise ValueError("SOURCE_REGISTRY_SOURCE_REVOKED_OR_INACTIVE")
    if not (
        {"READ_MESSAGE", "SEARCH"} & set(registration.capabilities)
    ):
        raise ValueError("SOURCE_REGISTRY_MAILBOX_READ_CAPABILITY_REQUIRED")
    return build_readonly_source_authority_v0(
        authority_id=f"source-authority:{registration.source_id}",
        provider=registration.provider,
        mailbox_identity_sha256=registration.source_identity_sha256,
        authority_reference=(
            f"source-registration:{registration.registration_hash}"
        ),
        approved_by=registration.approved_by,
    )


def _item_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "item_id",
        "source_id",
        "source_kind",
        "provider",
        "registration_hash",
        "provider_item_id_sha256",
        "content_sha256",
        "metadata_sha256",
        "observed_at",
        "raw_provider_item_id_persisted",
        "raw_content_persisted",
        "raw_source_identity_persisted",
        "allowed_to_decide",
        "allowed_to_act",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_readonly_source_item_v0(
    *,
    registration: OperationalSourceRegistrationV0,
    registry: OperationalSourceRegistryV0,
    provider_item_id: str,
    content: str,
    metadata: Mapping[str, Any],
    observed_at: str,
) -> ReadonlySourceItemV0:
    if not registry.is_active(registration.source_id):
        raise ValueError("SOURCE_REGISTRY_SOURCE_REVOKED_OR_INACTIVE")
    loaded = registry.load(registration.source_id)
    if loaded is None or loaded.registration_hash != registration.registration_hash:
        raise ValueError("SOURCE_REGISTRY_REGISTRATION_NOT_CANONICAL")
    if not provider_item_id:
        raise ValueError("SOURCE_ITEM_PROVIDER_ID_REQUIRED")
    _require_time(observed_at)
    provider_item_hash = hashlib.sha256(
        provider_item_id.encode("utf-8")
    ).hexdigest()
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    metadata_hash = _hash(dict(metadata))
    item_id = f"source-item:{_hash({
        'source': registration.registration_hash,
        'provider_item': provider_item_hash,
    })[:24]}"
    payload = {
        "schema": "CSSA_READONLY_SOURCE_ITEM_V0",
        "item_id": item_id,
        "source_id": registration.source_id,
        "source_kind": registration.source_kind,
        "provider": registration.provider,
        "registration_hash": registration.registration_hash,
        "provider_item_id_sha256": provider_item_hash,
        "content_sha256": content_hash,
        "metadata_sha256": metadata_hash,
        "observed_at": observed_at,
        "raw_provider_item_id_persisted": False,
        "raw_content_persisted": False,
        "raw_source_identity_persisted": False,
        "allowed_to_decide": False,
        "allowed_to_act": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    return ReadonlySourceItemV0(
        **payload,
        item_hash=_hash(payload),
    )


def verify_readonly_source_item_v0(
    item: ReadonlySourceItemV0 | Mapping[str, Any],
    *,
    registration: OperationalSourceRegistrationV0,
) -> tuple[bool, Optional[str]]:
    data = item.to_dict() if isinstance(item, ReadonlySourceItemV0) else dict(item)
    if data.get("schema") != "CSSA_READONLY_SOURCE_ITEM_V0":
        return False, "SOURCE_ITEM_SCHEMA_INVALID"
    if data.get("source_id") != registration.source_id:
        return False, "SOURCE_ITEM_SOURCE_ID_MISMATCH"
    if data.get("registration_hash") != registration.registration_hash:
        return False, "SOURCE_ITEM_REGISTRATION_HASH_MISMATCH"
    if data.get("source_kind") != registration.source_kind:
        return False, "SOURCE_ITEM_KIND_MISMATCH"
    if data.get("provider") != registration.provider:
        return False, "SOURCE_ITEM_PROVIDER_MISMATCH"
    if data.get("allowed_to_decide") is not False:
        return False, "SOURCE_ITEM_DECISION_FORBIDDEN"
    if data.get("allowed_to_act") is not False:
        return False, "SOURCE_ITEM_ACTION_FORBIDDEN"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_ITEM_AUTHORITY_INVALID"
    if any(
        (
            data.get("raw_provider_item_id_persisted"),
            data.get("raw_content_persisted"),
            data.get("raw_source_identity_persisted"),
        )
    ):
        return False, "SOURCE_ITEM_PRIVACY_BOUNDARY_VIOLATED"
    if _hash(_item_payload(data)) != data.get("item_hash"):
        return False, "SOURCE_ITEM_HASH_MISMATCH"
    return True, None
