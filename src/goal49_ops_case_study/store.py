"""Minimal atomic state store for the synthetic reference implementation."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_json
from .models import Snapshot

_SAFE_TARGET = re.compile(r"[^A-Za-z0-9_.-]+")


def safe_target(target: str) -> str:
    cleaned = _SAFE_TARGET.sub("_", target).strip("._")
    if not cleaned:
        raise ValueError("target does not contain a safe filename component")
    return cleaned


class JsonStateStore:
    """Write state atomically without retaining temporary files."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "snapshots").mkdir(exist_ok=True)
        (self.root / "decisions").mkdir(exist_ok=True)
        (self.root / "receipts").mkdir(exist_ok=True)
        (self.root / "outbox").mkdir(exist_ok=True)

    def _path(self, section: str, target: str, suffix: str) -> Path:
        return self.root / section / f"{safe_target(target)}{suffix}"

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(text)
            temp_name = handle.name
        os.replace(temp_name, path)

    def write_json(self, path: Path, value: Mapping[str, Any]) -> None:
        self._atomic_text(path, canonical_json(value) + "\n")

    def read_json(self, path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object at {path.name}")
        return value

    def snapshot_path(self, target: str) -> Path:
        return self._path("snapshots", target, ".json")

    def decision_path(self, target: str) -> Path:
        return self._path("decisions", target, ".json")

    def receipt_path(self, target: str) -> Path:
        return self._path("receipts", target, ".json")

    def outbox_path(self, target: str) -> Path:
        return self._path("outbox", target, ".txt")

    def write_snapshot(self, snapshot: Snapshot) -> None:
        self.write_json(self.snapshot_path(snapshot.target), snapshot.to_dict())

    def read_snapshot(self, target: str) -> Snapshot | None:
        value = self.read_json(self.snapshot_path(target))
        return None if value is None else Snapshot.from_dict(value)

    def write_decision(self, target: str, value: Mapping[str, Any]) -> None:
        self.write_json(self.decision_path(target), value)

    def read_receipt(self, target: str) -> dict[str, Any] | None:
        return self.read_json(self.receipt_path(target))

    def write_receipt(self, target: str, value: Mapping[str, Any]) -> None:
        self.write_json(self.receipt_path(target), value)

    def write_outbox(self, target: str, message: str) -> None:
        self._atomic_text(self.outbox_path(target), message.rstrip() + "\n")
