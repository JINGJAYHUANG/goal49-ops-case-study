# Reliability Controls and Residual Risk

## Failure-mode matrix

| ID | Failure mode | Preventive control | Detective control | Public proof | Residual risk |
|---|---|---|---|---|---|
| F01 | Ephemeral compute loses prior state | persist a minimal snapshot and receipt | health check reads durable state | store and health tests | persistence service can itself fail |
| F02 | Prepared inputs are modified | canonical payload digest | verify before finalization | tamper test | SHA-256 does not prove source truth |
| F03 | Provider returns old data | explicit freshness window | diagnostic records age/status | stale fallback test | provider timestamp can be wrong |
| F04 | Provider returns partial data | minimum coverage gate | coverage diagnostic | partial-provider test | high coverage does not ensure correctness |
| F05 | Provider outage | ordered independent fallback | provider-by-provider diagnostics | fallback test | correlated provider failure remains |
| F06 | Retry sends duplicate | stable visible-identity digest | persisted receipt comparison | duplicate test | non-atomic external send/receipt gap remains |
| F07 | Rerun produces a conflicting result | first receipt wins | conflict status | conflict test | operator must resolve legitimate corrections |
| F08 | Run starts too late | hard deadline | `late` terminal status | deadline test | clock or timezone misconfiguration |
| F09 | Preparation succeeds but delivery fails | separate stage health checks | post-deadline missing-receipt alert | health tests | alert channel can also fail |
| F10 | Debug details leak to users | separate renderer and outbox | privacy regression test | provider-leak test | new fields require review |
| F11 | Source or workflow drifts | pinned dependencies, tests and review | CI | workflow file | upstream platform behavior can change |
| F12 | Two workers race | shared production concurrency domain | receipt conflict | design documentation | file store alone is not transactional across hosts |

## Key invariants

### Invariant 1: preparation is immutable

After a snapshot is written, finalization consumes the exact verified payload or terminates with `integrity_error`.

### Invariant 2: freshness is explicit

No provider is accepted because it merely returned a response. Target, timestamp, uniqueness and coverage are all checked.

### Invariant 3: visible identity is stable

Operational metadata must not turn the same user-facing result into a second delivery.

### Invariant 4: late recovery cannot manufacture a current decision

After the hard deadline, the only allowed result is a status-only terminal message. This is safer than producing an apparently current result from late data.

### Invariant 5: stage health is independent

Preparation health and final-delivery health are different checks. A valid snapshot is not evidence that a final receipt exists.

## Exactly-once terminology

This project intentionally says **idempotent delivery guard**, not mathematically guaranteed exactly-once delivery. If an external message succeeds and the process crashes before writing the receipt, a retry can still duplicate it. Production mitigation options include:

- destination-supported idempotency keys;
- transactional outbox plus dispatcher;
- durable queue with deduplication;
- a store that atomically commits message intent and receipt state.

The file-backed simulator is sufficient to demonstrate the identity model, not to solve every distributed-systems failure.
