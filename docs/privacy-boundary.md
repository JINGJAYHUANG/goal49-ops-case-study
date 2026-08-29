# Privacy and Publication Boundary

## Purpose

The source system is private. This repository publishes transferable reliability lessons while preventing reconstruction of its decision logic or operating context.

## Allowed public material

- abstract architecture and state transitions;
- generic failure modes and mitigations;
- synthetic item IDs and fixture timestamps;
- canonical hashing, receipt and health-check code;
- sanitized incident chronology;
- test results generated from this public repository;
- limitations and unresolved distributed-systems risks.

## Prohibited material

- model factors, directions, weights, gates, thresholds or candidate rules;
- real instrument identifiers, prices, scores, recommendations or performance;
- actual data-source credentials, request parameters or private endpoints;
- actual messaging endpoints, recipients or group names;
- real state files, logs, artifacts or screenshots;
- private repository URLs, branches, commit hashes or issue discussions;
- personal identity records, machine paths, customer data or counterparties;
- claims of guaranteed execution, returns, uptime or exactly-once delivery.

## De-identification choices

| Private concept | Public representation |
|---|---|
| candidate instrument | `ITEM-001` |
| business date | `DEMO-2026-01-15` |
| live market field | boolean fixture eligibility |
| named external provider | `provider-a`, `provider-b` |
| message destination | local `outbox/` file |
| production state branch | local JSON state store |
| production deadline | synthetic UTC timestamp |

## Review gate

Before merging a public change:

1. run `python scripts/public_audit.py .`;
2. inspect the diff for business-rule leakage, not only secrets;
3. confirm all example values are synthetic;
4. confirm every operational claim is in `docs/evidence-register.md`;
5. reject performance language unsupported by public evidence.

Automated scanning reduces accidental disclosure but cannot recognize every proprietary idea. Human review remains mandatory.
