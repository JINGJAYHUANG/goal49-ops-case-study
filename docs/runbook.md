# Synthetic Demo Runbook

This runbook applies only to the public, network-free simulator.

## 1. Preflight

```bash
python --version
python -m compileall -q src scripts tests
python -m unittest discover -s tests -v
python scripts/public_audit.py .
```

Expected: Python 3.11 or later, all tests pass, and the public audit reports zero findings.

## 2. Clean demonstration

```bash
rm -rf .demo
python -m goal49_ops_case_study.cli run-demo \
  --config examples/synthetic-config.json \
  --universe examples/synthetic-universe.json \
  --workdir .demo
```

Expected decision:

- `provider-a` rejected as stale;
- `provider-b` accepted;
- four abstract items selected in prepared order;
- `delivery_action` equals `deliver`;
- snapshot, decision, receipt and outbox files exist.

## 3. Idempotency demonstration

Repeat the same command against `.demo`.

Expected: `delivery_action` equals `duplicate_skipped`; no second outbox identity is created.

## 4. Snapshot verification

```bash
python -m goal49_ops_case_study.cli verify \
  --workdir .demo \
  --target DEMO-2026-01-15
```

Expected: status `verified` and the stored digest.

## 5. Health checks

Preparation:

```bash
python -m goal49_ops_case_study.cli health \
  --workdir .demo \
  --target DEMO-2026-01-15 \
  --stage prepare \
  --checked-at 2026-01-15T00:30:00Z \
  --deadline 2026-01-15T01:05:00Z
```

Final delivery:

```bash
python -m goal49_ops_case_study.cli health \
  --workdir .demo \
  --target DEMO-2026-01-15 \
  --stage final \
  --checked-at 2026-01-15T01:06:00Z \
  --deadline 2026-01-15T01:05:00Z
```

Expected: both healthy after the clean demo run.

## 6. Incident handling

| Symptom | Interpretation | Safe action |
|---|---|---|
| missing snapshot | preparation did not persist | request preparation recovery |
| digest mismatch | state was changed or corrupted | reject and rebuild preparation |
| all providers rejected | no trustworthy live batch | deliver unavailable status only |
| decision time after deadline | result would be stale | deliver late status only |
| same receipt digest | retry of same visible result | skip duplicate |
| different receipt digest | conflicting rerun | block and escalate |
| no receipt after deadline | end-to-end delivery failed | raise operational alert; do not create a late decision |
