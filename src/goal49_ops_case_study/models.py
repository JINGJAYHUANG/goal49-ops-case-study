"""Typed models for a deterministic, network-free reliability simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

UTC = timezone.utc


def parse_utc(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(UTC)


def format_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class PreparedItem:
    item_id: str
    rank: int

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PreparedItem":
        item_id = str(value.get("item_id", "")).strip()
        rank = int(value.get("rank", 0))
        if not item_id:
            raise ValueError("item_id is required")
        if rank < 1:
            raise ValueError("rank must be positive")
        return cls(item_id=item_id, rank=rank)

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "rank": self.rank}


@dataclass(frozen=True, slots=True)
class Snapshot:
    schema_version: str
    target: str
    source_revision: str
    prepared_at: str
    items: tuple[PreparedItem, ...]
    digest: str

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "target": self.target,
            "source_revision": self.source_revision,
            "prepared_at": self.prepared_at,
            "items": [item.to_dict() for item in self.items],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "digest": self.digest}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Snapshot":
        raw_items = value.get("items", [])
        if not isinstance(raw_items, Iterable) or isinstance(raw_items, (str, bytes)):
            raise ValueError("items must be a list")
        return cls(
            schema_version=str(value.get("schema_version", "")),
            target=str(value.get("target", "")),
            source_revision=str(value.get("source_revision", "")),
            prepared_at=str(value.get("prepared_at", "")),
            items=tuple(PreparedItem.from_dict(item) for item in raw_items),
            digest=str(value.get("digest", "")),
        )


@dataclass(frozen=True, slots=True)
class Observation:
    item_id: str
    eligible: bool

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Observation":
        item_id = str(value.get("item_id", "")).strip()
        if not item_id:
            raise ValueError("observation item_id is required")
        eligible = value.get("eligible")
        if not isinstance(eligible, bool):
            raise ValueError("eligible must be boolean")
        return cls(item_id=item_id, eligible=eligible)

    def to_dict(self) -> dict[str, Any]:
        return {"item_id": self.item_id, "eligible": self.eligible}


@dataclass(frozen=True, slots=True)
class ProviderBatch:
    provider: str
    target: str
    observed_at: str
    observations: tuple[Observation, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ProviderBatch":
        provider = str(value.get("provider", "")).strip()
        target = str(value.get("target", "")).strip()
        observed_at = str(value.get("observed_at", "")).strip()
        if not provider or not target or not observed_at:
            raise ValueError("provider, target and observed_at are required")
        parse_utc(observed_at)
        raw = value.get("observations", [])
        if not isinstance(raw, list):
            raise ValueError("observations must be a list")
        return cls(
            provider=provider,
            target=target,
            observed_at=observed_at,
            observations=tuple(Observation.from_dict(item) for item in raw),
        )


@dataclass(frozen=True, slots=True)
class Decision:
    target: str
    status: str
    selected_items: tuple[str, ...]
    provider: str | None
    coverage: float
    delivery_digest: str
    delivery_action: str
    decided_at: str
    diagnostics: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "status": self.status,
            "selected_items": list(self.selected_items),
            "provider": self.provider,
            "coverage": round(self.coverage, 6),
            "delivery_digest": self.delivery_digest,
            "delivery_action": self.delivery_action,
            "decided_at": self.decided_at,
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True, slots=True)
class HealthResult:
    target: str
    stage: str
    status: str
    action: str
    checked_at: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "target": self.target,
            "stage": self.stage,
            "status": self.status,
            "action": self.action,
            "checked_at": self.checked_at,
            "detail": self.detail,
        }
