# ADR-002: Hash User-Visible Identity, Not Volatile Diagnostics

- Status: Accepted
- Date: 2026-08-29

## Context

A retry may use a different provider, timing path or diagnostic detail while producing the same message. Hashing the entire internal payload would treat that retry as a new delivery.

## Decision

Compute the delivery digest from target, terminal status and selected abstract IDs only. Persist one receipt per target. Skip the same digest and block a different digest after a receipt exists.

## Consequences

- fallback providers do not create duplicate user messages;
- operational diagnostics remain available in the decision record;
- legitimate post-delivery corrections require explicit operator handling;
- the approach is idempotent but is not a proof of distributed exactly-once delivery.
