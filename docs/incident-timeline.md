# Sanitized Incident Timeline

This chronology records operational evolution only. It intentionally omits the private model, real inputs, exact business thresholds, recipients and raw logs.

| Date | Sanitized event | Reliability lesson | Resulting control |
|---|---|---|---|
| 2026-08-11 | Initial scheduled cloud deployment was established. | A scheduled script is not yet an operational system. | explicit state, setup documentation and basic guardrails |
| 2026-08-15 | Runtime hardening separated the frozen decision source from operational wrappers. | Reliability changes must not silently alter business logic. | source-boundary checks, stable delivery identity and pull-request tests |
| 2026-08-27 | Final-stage confirmation, multiple input providers and an independent health monitor were added. | Live inputs require freshness, coverage and fallback semantics; preparation and delivery need separate health checks. | provider gate, receipt-aware health checks and integrity manifests |
| 2026-08-28 | A final delivery was missed even though earlier stages existed. | Independent scheduled stages can fail to rendezvous on ephemeral infrastructure. A green preparation stage is not proof of final delivery. | anchor the final stage to an already-running path, retain redundant fallbacks and enforce a hard deadline |
| 2026-08-29 | The public case study was extracted. | Public evidence must show controls without publishing private strategy or pretending synthetic tests are production metrics. | abstract simulator, privacy boundary, evidence register and claim limitations |

## Sanitized root-cause analysis of the missed delivery

### Observed symptom

No final receipt was present after the intended delivery window.

### Contributing conditions

- preparation and finalization were separate scheduled activities;
- hosted compute instances did not share local disk state;
- schedule timing was a platform behavior, not a hard real-time guarantee;
- earlier-stage success could be mistaken for end-to-end success.

### Remediation pattern

1. persist the complete minimum final-stage input;
2. reserve a long-running execution path before the live window;
3. retain independent schedule anchors as fallback, not as the only path;
4. require fresh target-day inputs and minimum coverage;
5. prohibit decision generation after the hard deadline;
6. persist a final delivery receipt;
7. alert on a missing receipt instead of generating a stale decision.

## What is not claimed

No uptime percentage, mean-time-to-recovery, latency percentile or business-performance improvement is claimed. The internal history proves that the failure mode occurred and that controls were implemented; the public simulator proves only the documented control semantics.
