#!/usr/bin/env python3
"""Fail when the public tree contains common secrets or private identifiers."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
    ".txt",
    ".cff",
}
SKIP_PARTS = {".git", ".venv", "venv", "build", "dist", ".demo", "__pycache__"}
SKIP_FILES = {"public_audit.py"}

PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "github-fine-grained-token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "openai-style-secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "webhook-url": re.compile(r"https://[^\s\"']+(?:webhook|hook)[^\s\"']*", re.I),
    "windows-user-path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.I),
    "mac-user-path": re.compile(r"/Users/[^/\s]+"),
    "linux-user-path": re.compile(r"/home/[^/\s]+"),
    "a-share-symbol": re.compile(r"\b\d{6}\.(?:SH|SZ)\b"),
}

PROHIBITED_TERMS = (
    "TUSHARE_TOKEN",
    "FEISHU_WEBHOOK_URL",
    "goal49-cloud-morning",
)


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_FILES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "LICENSE":
            continue
        yield path


def audit(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"binary-or-non-utf8:{path.relative_to(root)}")
            continue
        relative = path.relative_to(root)
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{name}:{relative}")
        for term in PROHIBITED_TERMS:
            if term in text:
                findings.append(f"prohibited-term:{term}:{relative}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    root = args.root.resolve()
    findings = audit(root)
    if findings:
        for finding in findings:
            print(finding)
        print(f"public audit failed with {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print(f"public audit passed: {sum(1 for _ in iter_text_files(root))} text files scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
