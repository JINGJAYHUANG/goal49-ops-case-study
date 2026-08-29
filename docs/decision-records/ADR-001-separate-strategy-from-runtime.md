# ADR-001: Separate Private Decision Logic from Runtime Reliability

- Status: Accepted
- Date: 2026-08-29

## Context

Operational hardening can accidentally change business behavior when scheduling, state, delivery and selection live in one module. A public case study also must not disclose the private decision model.

## Decision

Represent the private stage as an already ordered list of abstract item IDs. The public code may verify, persist and finalize those IDs, but it does not implement or approximate private factors, gates, thresholds or ranking logic.

## Consequences

- reliability controls can be tested independently;
- public code cannot reproduce the private model;
- changes to operations have a smaller semantic surface;
- the simulator is not a backtest and cannot support performance claims.
