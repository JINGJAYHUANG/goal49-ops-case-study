# ADR-003: Prefer Status-Only Failure after a Hard Deadline

- Status: Accepted
- Date: 2026-08-29

## Context

A delayed scheduler or unavailable provider may recover after the business window. Generating a normal-looking decision at that point can be more harmful than reporting failure.

## Decision

After the configured deadline, do not evaluate provider observations or select items. Produce a terminal `late` status with no selected items and record it through the same delivery guard.

## Consequences

- late data cannot masquerade as timely data;
- the system fails visibly rather than silently;
- availability is intentionally sacrificed to preserve temporal validity;
- applications without a hard validity window may choose a different policy.
