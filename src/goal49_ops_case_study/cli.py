"""Command-line interface for the public synthetic case study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .engine import build_snapshot, finalize, health_check, verify_snapshot
from .models import PreparedItem, ProviderBatch, parse_utc
from .store import JsonStateStore


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_stdout(value: Any) -> None:
    print(canonical_json(value))


def run_demo(args: argparse.Namespace) -> int:
    config = _load_json(args.config)
    universe = _load_json(args.universe)
    if not isinstance(config, dict) or not isinstance(universe, list):
        raise ValueError("config must be an object and universe must be a list")

    store = JsonStateStore(args.workdir)
    snapshot = build_snapshot(
        target=str(config["target"]),
        source_revision=str(config["source_revision"]),
        prepared_at=parse_utc(str(config["prepared_at"])),
        items=(PreparedItem.from_dict(item) for item in universe),
    )
    store.write_snapshot(snapshot)
    providers = tuple(ProviderBatch.from_dict(value) for value in config["providers"])
    decision = finalize(
        snapshot=snapshot,
        providers=providers,
        decision_time=parse_utc(str(config["decision_time"])),
        deadline=parse_utc(str(config["deadline"])),
        freshness_seconds=int(config["freshness_seconds"]),
        minimum_coverage=float(config["minimum_coverage"]),
        max_items=int(config["max_items"]),
        store=store,
    )
    _write_stdout(decision.to_dict())
    return 0


def verify(args: argparse.Namespace) -> int:
    store = JsonStateStore(args.workdir)
    snapshot = store.read_snapshot(args.target)
    if snapshot is None:
        _write_stdout({"target": args.target, "status": "missing"})
        return 2
    verify_snapshot(snapshot)
    _write_stdout({"target": args.target, "status": "verified", "digest": snapshot.digest})
    return 0


def run_health(args: argparse.Namespace) -> int:
    store = JsonStateStore(args.workdir)
    result = health_check(
        store=store,
        target=args.target,
        stage=args.stage,
        checked_at=parse_utc(args.checked_at),
        deadline=parse_utc(args.deadline),
    )
    _write_stdout(result.to_dict())
    return 0 if result.status in {"healthy", "pending"} else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goal49-ops-demo",
        description="Run the network-free synthetic reliability case study.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("run-demo", help="run the deterministic synthetic scenario")
    demo.add_argument("--config", type=Path, required=True)
    demo.add_argument("--universe", type=Path, required=True)
    demo.add_argument("--workdir", type=Path, required=True)
    demo.set_defaults(func=run_demo)

    verify_parser = subparsers.add_parser("verify", help="verify a stored snapshot digest")
    verify_parser.add_argument("--workdir", type=Path, required=True)
    verify_parser.add_argument("--target", required=True)
    verify_parser.set_defaults(func=verify)

    health = subparsers.add_parser("health", help="evaluate preparation or final-delivery health")
    health.add_argument("--workdir", type=Path, required=True)
    health.add_argument("--target", required=True)
    health.add_argument("--stage", choices=("prepare", "final"), required=True)
    health.add_argument("--checked-at", required=True)
    health.add_argument("--deadline", required=True)
    health.set_defaults(func=run_health)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
