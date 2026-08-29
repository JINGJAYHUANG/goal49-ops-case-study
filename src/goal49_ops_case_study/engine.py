"""Reliability controls extracted into a synthetic, non-financial simulator."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Sequence

from .canonical import sha256_json
from .models import (
    Decision,
    HealthResult,
    PreparedItem,
    ProviderBatch,
    Snapshot,
    format_utc,
    parse_utc,
)
from .store import JsonStateStore

SNAPSHOT_SCHEMA = "goal49-ops-public-snapshot-v1"


class IntegrityError(ValueError):
    """Raised when a persisted snapshot no longer matches its digest."""


def _normalize_items(items: Iterable[PreparedItem]) -> tuple[PreparedItem, ...]:
    normalized = tuple(sorted(items, key=lambda item: (item.rank, item.item_id)))
    if not normalized:
        raise ValueError("at least one prepared item is required")
    ids = [item.item_id for item in normalized]
    ranks = [item.rank for item in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("prepared item IDs must be unique")
    if len(ranks) != len(set(ranks)):
        raise ValueError("prepared ranks must be unique")
    return normalized


def build_snapshot(
    *,
    target: str,
    source_revision: str,
    prepared_at: datetime,
    items: Iterable[PreparedItem],
) -> Snapshot:
    target = target.strip()
    source_revision = source_revision.strip()
    if not target or not source_revision:
        raise ValueError("target and source_revision are required")
    normalized = _normalize_items(items)
    unsigned = {
        "schema_version": SNAPSHOT_SCHEMA,
        "target": target,
        "source_revision": source_revision,
        "prepared_at": format_utc(prepared_at),
        "items": [item.to_dict() for item in normalized],
    }
    return Snapshot(
        schema_version=SNAPSHOT_SCHEMA,
        target=target,
        source_revision=source_revision,
        prepared_at=unsigned["prepared_at"],
        items=normalized,
        digest=sha256_json(unsigned),
    )


def verify_snapshot(snapshot: Snapshot) -> None:
    if snapshot.schema_version != SNAPSHOT_SCHEMA:
        raise IntegrityError("unsupported snapshot schema")
    parse_utc(snapshot.prepared_at)
    _normalize_items(snapshot.items)
    expected = sha256_json(snapshot.unsigned_dict())
    if expected != snapshot.digest:
        raise IntegrityError("snapshot digest mismatch")


def _provider_diagnostic(
    batch: ProviderBatch,
    snapshot: Snapshot,
    now: datetime,
    freshness_seconds: int,
    minimum_coverage: float,
) -> tuple[bool, float, dict[str, Any]]:
    diagnostic: dict[str, Any] = {"provider": batch.provider}
    if batch.target != snapshot.target:
        diagnostic.update(status="wrong_target", coverage=0.0)
        return False, 0.0, diagnostic

    observed_at = parse_utc(batch.observed_at)
    age_seconds = (now - observed_at).total_seconds()
    if age_seconds < 0:
        diagnostic.update(status="future_timestamp", coverage=0.0)
        return False, 0.0, diagnostic
    if age_seconds > freshness_seconds:
        diagnostic.update(
            status="stale",
            age_seconds=int(age_seconds),
            coverage=0.0,
        )
        return False, 0.0, diagnostic

    observations = list(batch.observations)
    observed_ids = [item.item_id for item in observations]
    if len(observed_ids) != len(set(observed_ids)):
        diagnostic.update(status="duplicate_observation", coverage=0.0)
        return False, 0.0, diagnostic

    prepared_ids = {item.item_id for item in snapshot.items}
    covered = len(prepared_ids.intersection(observed_ids))
    coverage = covered / len(prepared_ids)
    if coverage < minimum_coverage:
        diagnostic.update(status="insufficient_coverage", coverage=round(coverage, 6))
        return False, coverage, diagnostic

    diagnostic.update(
        status="accepted",
        age_seconds=int(age_seconds),
        coverage=round(coverage, 6),
    )
    return True, coverage, diagnostic


def _visible_identity(target: str, status: str, selected: Sequence[str]) -> dict[str, Any]:
    return {"target": target, "status": status, "selected_items": list(selected)}


def render_message(target: str, status: str, selected: Sequence[str]) -> str:
    lines = [f"Synthetic final result | {target}", f"status: {status}"]
    if selected:
        lines.append("items:")
        lines.extend(f"- {item_id}" for item_id in selected)
    return "\n".join(lines)


def _commit_delivery(
    *,
    store: JsonStateStore,
    target: str,
    status: str,
    selected: tuple[str, ...],
    decided_at: datetime,
) -> tuple[str, str]:
    digest = sha256_json(_visible_identity(target, status, selected))
    previous = store.read_receipt(target)
    if previous is not None:
        previous_digest = str(previous.get("delivery_digest", ""))
        if previous_digest == digest:
            return digest, "duplicate_skipped"
        return digest, "blocked_receipt_conflict"

    store.write_receipt(
        target,
        {
            "target": target,
            "status": status,
            "selected_items": list(selected),
            "delivery_digest": digest,
            "delivered_at": format_utc(decided_at),
        },
    )
    store.write_outbox(target, render_message(target, status, selected))
    return digest, "deliver"


def finalize(
    *,
    snapshot: Snapshot,
    providers: Sequence[ProviderBatch],
    decision_time: datetime,
    deadline: datetime,
    freshness_seconds: int,
    minimum_coverage: float,
    max_items: int,
    store: JsonStateStore,
) -> Decision:
    if freshness_seconds < 0:
        raise ValueError("freshness_seconds must be non-negative")
    if not 0 <= minimum_coverage <= 1:
        raise ValueError("minimum_coverage must be between 0 and 1")
    if max_items < 1:
        raise ValueError("max_items must be positive")

    diagnostics: list[dict[str, Any]] = []
    provider_name: str | None = None
    coverage = 0.0
    selected: tuple[str, ...] = ()

    try:
        verify_snapshot(snapshot)
    except (IntegrityError, ValueError) as exc:
        status = "integrity_error"
        diagnostics.append({"status": "snapshot_rejected", "reason": str(exc)})
    else:
        if decision_time > deadline:
            status = "late"
            diagnostics.append({"status": "deadline_passed"})
        else:
            accepted_batch: ProviderBatch | None = None
            for batch in providers:
                accepted, batch_coverage, diagnostic = _provider_diagnostic(
                    batch,
                    snapshot,
                    decision_time,
                    freshness_seconds,
                    minimum_coverage,
                )
                diagnostics.append(diagnostic)
                if accepted:
                    accepted_batch = batch
                    coverage = batch_coverage
                    provider_name = batch.provider
                    break

            if accepted_batch is None:
                status = "unavailable"
            else:
                eligibility = {
                    observation.item_id: observation.eligible
                    for observation in accepted_batch.observations
                }
                selected = tuple(
                    item.item_id
                    for item in snapshot.items
                    if eligibility.get(item.item_id) is True
                )[:max_items]
                status = "selected" if selected else "none"

    digest, action = _commit_delivery(
        store=store,
        target=snapshot.target,
        status=status,
        selected=selected,
        decided_at=decision_time,
    )
    if action == "blocked_receipt_conflict":
        diagnostics.append({"status": "existing_receipt_has_different_identity"})

    decision = Decision(
        target=snapshot.target,
        status=status,
        selected_items=selected,
        provider=provider_name,
        coverage=coverage,
        delivery_digest=digest,
        delivery_action=action,
        decided_at=format_utc(decision_time),
        diagnostics=tuple(diagnostics),
    )
    store.write_decision(snapshot.target, decision.to_dict())
    return decision


def health_check(
    *,
    store: JsonStateStore,
    target: str,
    stage: str,
    checked_at: datetime,
    deadline: datetime,
) -> HealthResult:
    if stage not in {"prepare", "final"}:
        raise ValueError("stage must be 'prepare' or 'final'")

    if stage == "prepare":
        snapshot = store.read_snapshot(target)
        if snapshot is None:
            return HealthResult(
                target,
                stage,
                "degraded",
                "dispatch_prepare",
                format_utc(checked_at),
                "prepared snapshot is missing",
            )
        try:
            verify_snapshot(snapshot)
        except (IntegrityError, ValueError):
            return HealthResult(
                target,
                stage,
                "degraded",
                "dispatch_prepare",
                format_utc(checked_at),
                "prepared snapshot failed integrity verification",
            )
        return HealthResult(
            target,
            stage,
            "healthy",
            "none",
            format_utc(checked_at),
            "prepared snapshot is present and verified",
        )

    receipt = store.read_receipt(target)
    if receipt is not None:
        return HealthResult(
            target,
            stage,
            "healthy",
            "none",
            format_utc(checked_at),
            "final delivery receipt is present",
        )
    if checked_at <= deadline:
        return HealthResult(
            target,
            stage,
            "pending",
            "none",
            format_utc(checked_at),
            "final delivery window remains open",
        )
    return HealthResult(
        target,
        stage,
        "degraded",
        "raise_operational_alert",
        format_utc(checked_at),
        "final delivery receipt is missing after the deadline",
    )
