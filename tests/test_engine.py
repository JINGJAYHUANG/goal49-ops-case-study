from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from goal49_ops_case_study.engine import (
    IntegrityError,
    build_snapshot,
    finalize,
    health_check,
    verify_snapshot,
)
from goal49_ops_case_study.models import Observation, PreparedItem, ProviderBatch
from goal49_ops_case_study.store import JsonStateStore

UTC = timezone.utc


def dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2026, 1, 15, hour, minute, second, tzinfo=UTC)


def items(count: int = 4) -> tuple[PreparedItem, ...]:
    return tuple(PreparedItem(f"ITEM-{index:03d}", index) for index in range(1, count + 1))


def batch(
    name: str,
    observed_at: str,
    values: list[tuple[str, bool]],
    target: str = "DEMO",
) -> ProviderBatch:
    return ProviderBatch(
        provider=name,
        target=target,
        observed_at=observed_at,
        observations=tuple(Observation(item_id, eligible) for item_id, eligible in values),
    )


class SnapshotTests(unittest.TestCase):
    def test_snapshot_hash_is_deterministic(self) -> None:
        first = build_snapshot(
            target="DEMO",
            source_revision="v1",
            prepared_at=dt(0),
            items=reversed(items()),
        )
        second = build_snapshot(
            target="DEMO",
            source_revision="v1",
            prepared_at=dt(0),
            items=items(),
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_duplicate_ids_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_snapshot(
                target="DEMO",
                source_revision="v1",
                prepared_at=dt(0),
                items=(PreparedItem("A", 1), PreparedItem("A", 2)),
            )

    def test_tampering_is_detected(self) -> None:
        snapshot = build_snapshot(
            target="DEMO",
            source_revision="v1",
            prepared_at=dt(0),
            items=items(),
        )
        tampered = replace(snapshot, source_revision="v2")
        with self.assertRaises(IntegrityError):
            verify_snapshot(tampered)


class FinalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = JsonStateStore(self.temp.name)
        self.snapshot = build_snapshot(
            target="DEMO",
            source_revision="v1",
            prepared_at=dt(0),
            items=items(),
        )
        self.store.write_snapshot(self.snapshot)

    def finalize(self, providers, decision_time=dt(1), deadline=dt(1, 5)):
        return finalize(
            snapshot=self.snapshot,
            providers=providers,
            decision_time=decision_time,
            deadline=deadline,
            freshness_seconds=180,
            minimum_coverage=0.75,
            max_items=3,
            store=self.store,
        )

    def test_fallback_skips_stale_provider(self) -> None:
        decision = self.finalize(
            [
                batch("stale", "2026-01-15T00:50:00Z", [(i.item_id, True) for i in items()]),
                batch(
                    "fresh",
                    "2026-01-15T00:59:30Z",
                    [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", True)],
                ),
            ]
        )
        self.assertEqual(decision.provider, "fresh")
        self.assertEqual(decision.selected_items, ("ITEM-001", "ITEM-003"))
        self.assertEqual(decision.delivery_action, "deliver")
        self.assertEqual(decision.diagnostics[0]["status"], "stale")

    def test_insufficient_coverage_is_rejected(self) -> None:
        decision = self.finalize(
            [batch("partial", "2026-01-15T00:59:30Z", [("ITEM-001", True)])]
        )
        self.assertEqual(decision.status, "unavailable")
        self.assertEqual(decision.delivery_action, "deliver")

    def test_late_run_emits_status_only(self) -> None:
        decision = self.finalize([], decision_time=dt(1, 6))
        self.assertEqual(decision.status, "late")
        self.assertEqual(decision.selected_items, ())
        self.assertIsNone(decision.provider)

    def test_duplicate_delivery_is_suppressed(self) -> None:
        providers = [
            batch(
                "fresh",
                "2026-01-15T00:59:30Z",
                [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", True)],
            )
        ]
        first = self.finalize(providers)
        second = self.finalize(providers)
        self.assertEqual(first.delivery_digest, second.delivery_digest)
        self.assertEqual(second.delivery_action, "duplicate_skipped")

    def test_conflicting_second_delivery_is_blocked(self) -> None:
        first = self.finalize(
            [
                batch(
                    "fresh",
                    "2026-01-15T00:59:30Z",
                    [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", False)],
                )
            ]
        )
        second = self.finalize(
            [
                batch(
                    "fresh",
                    "2026-01-15T00:59:30Z",
                    [("ITEM-001", False), ("ITEM-002", True), ("ITEM-003", False)],
                )
            ]
        )
        self.assertNotEqual(first.delivery_digest, second.delivery_digest)
        self.assertEqual(second.delivery_action, "blocked_receipt_conflict")

    def test_provider_diagnostics_do_not_change_delivery_identity(self) -> None:
        first = self.finalize(
            [
                batch(
                    "provider-one",
                    "2026-01-15T00:59:30Z",
                    [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", True)],
                )
            ]
        )
        Path(self.store.receipt_path("DEMO")).unlink()
        second = self.finalize(
            [
                batch(
                    "provider-two",
                    "2026-01-15T00:59:45Z",
                    [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", True)],
                )
            ]
        )
        self.assertEqual(first.delivery_digest, second.delivery_digest)

    def test_outbox_contains_no_provider_diagnostics(self) -> None:
        self.finalize(
            [
                batch(
                    "internal-provider-name",
                    "2026-01-15T00:59:30Z",
                    [("ITEM-001", True), ("ITEM-002", False), ("ITEM-003", True)],
                )
            ]
        )
        message = self.store.outbox_path("DEMO").read_text(encoding="utf-8")
        self.assertNotIn("internal-provider-name", message)
        self.assertIn("ITEM-001", message)


class HealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = JsonStateStore(self.temp.name)

    def test_missing_snapshot_dispatches_recovery(self) -> None:
        result = health_check(
            store=self.store,
            target="DEMO",
            stage="prepare",
            checked_at=dt(0, 30),
            deadline=dt(1, 5),
        )
        self.assertEqual(result.action, "dispatch_prepare")

    def test_verified_snapshot_is_healthy(self) -> None:
        snapshot = build_snapshot(
            target="DEMO",
            source_revision="v1",
            prepared_at=dt(0),
            items=items(),
        )
        self.store.write_snapshot(snapshot)
        result = health_check(
            store=self.store,
            target="DEMO",
            stage="prepare",
            checked_at=dt(0, 30),
            deadline=dt(1, 5),
        )
        self.assertEqual(result.status, "healthy")

    def test_final_missing_before_deadline_is_pending(self) -> None:
        result = health_check(
            store=self.store,
            target="DEMO",
            stage="final",
            checked_at=dt(1, 3),
            deadline=dt(1, 5),
        )
        self.assertEqual(result.status, "pending")

    def test_final_missing_after_deadline_alerts(self) -> None:
        result = health_check(
            store=self.store,
            target="DEMO",
            stage="final",
            checked_at=dt(1, 6),
            deadline=dt(1, 5),
        )
        self.assertEqual(result.action, "raise_operational_alert")

    def test_receipt_makes_final_stage_healthy(self) -> None:
        self.store.write_receipt(
            "DEMO",
            {
                "target": "DEMO",
                "delivery_digest": "abc",
                "delivered_at": "2026-01-15T01:00:00Z",
            },
        )
        result = health_check(
            store=self.store,
            target="DEMO",
            stage="final",
            checked_at=dt(1, 6),
            deadline=dt(1, 5),
        )
        self.assertEqual(result.status, "healthy")


class StoreTests(unittest.TestCase):
    def test_json_is_canonical_and_newline_terminated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = JsonStateStore(temp)
            store.write_receipt("DEMO", {"z": 1, "a": 2})
            text = store.receipt_path("DEMO").read_text(encoding="utf-8")
            self.assertEqual(text, '{"a":2,"z":1}\n')

    def test_stored_decision_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = JsonStateStore(temp)
            store.write_decision("DEMO", {"status": "ok"})
            value = json.loads(store.decision_path("DEMO").read_text(encoding="utf-8"))
            self.assertEqual(value["status"], "ok")


if __name__ == "__main__":
    unittest.main()
