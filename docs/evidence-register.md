# Evidence Register

## Evidence classes

- **A — Public executable:** directly inspectable or reproducible in this repository.
- **B — Sanitized internal:** supported by the private source system or its history, but raw evidence is not published.
- **C — Design inference:** engineering judgment derived from A/B evidence; not a measured result.

## Claims

| ID | Claim | Class | Evidence | Limitation |
|---|---|---:|---|---|
| C01 | A prepared payload can be made tamper-evident with canonical serialization and a digest. | A | `build_snapshot`, `verify_snapshot`, tamper test | does not prove source data are true |
| C02 | A stale first provider can be rejected and a later provider accepted deterministically. | A | provider gate and fallback test | providers are synthetic |
| C03 | User-visible identity can remain stable when provider diagnostics change. | A | delivery-digest test | external transport is not exercised |
| C04 | Duplicate results can be suppressed and conflicting second results blocked after a receipt exists. | A | duplicate and conflict tests | file-backed receipt is not a distributed transaction |
| C05 | Preparation and final delivery require separate health checks. | A/B | public health tests; sanitized internal incident history | no production availability metric is published |
| C06 | A missed final delivery occurred after earlier-stage automation existed. | B | sanitized internal repository history | raw logs and private references are withheld |
| C07 | Anchoring the final stage to an already-running execution path reduces dependence on a just-in-time scheduler. | C | incident analysis and architecture | reduction is not quantified here |
| C08 | A hard deadline is safer than generating a stale late decision. | A/C | public late-run behavior; design rationale | business suitability depends on the application |
| C09 | The public repository contains no intended private model or real operating data. | A | source review plus `scripts/public_audit.py` | automated audit cannot prove absence of every sensitive concept |
| C10 | Clean demo runs are byte-for-byte deterministic. | A | CI executes two clean runs and diffs directories | determinism applies to the synthetic reference path |
