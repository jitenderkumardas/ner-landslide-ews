# ADR: Risk Tiering for AI-Assisted Development

**Status:** Accepted
**Date:** 2026-08 (pilot phase, East Khasi Hills corridor)

## Decision

Code in this repository is classified into tiers that determine review rigor, per the secure-SDLC approach adopted for this project:

| Path                                                                                    | Tier                               | Review requirement                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/risk_engine/`                                                                 | 0/1 — Safety/Availability-critical | 2 reviewers once team > 1; solo-dev substitute: mandatory re-review after a break, never same-session merge. Any threshold/weight/fusion change must be called out explicitly in the PR, not buried in a diff. |
| `services/alerting/`                                                                    | 0/1                                | Same as above. Alert severity mapping must match `docs/adr/alert-policy.md` (not yet defined — see that file).                                                                                                 |
| `services/ingestion/`, `services/api_gateway/`, `services/gis_dashboard/`, `field-app/` | 2                                  | Standard 1-reviewer PR flow. Must preserve provenance fields regardless of tier.                                                                                                                               |
| `docs/`, `infra/` non-prod configs                                                      | 3                                  | Lightweight review.                                                                                                                                                                                            |

## Why

This system's risk assessments are intended to eventually inform real evacuation/response decisions (see `docs/phases/` Phase 1 purpose). The cost of an undetected logic error in `risk_engine/` or `alerting/` is categorically different from a bug in the dashboard UI, so review effort should scale with that, not be uniform across the whole codebase.

## Consequences

- Slower iteration on `risk_engine/` and `alerting/` by design — this is accepted, not a bug in the process.
- Once a second contributor joins, branch protection should be updated to require an actual second approval for PRs touching these paths (GitHub CODEOWNERS + required review, or a path-based ruleset if the repo moves to an org/Team plan).
- Every threshold or model change in Tier 0/1 code must have a corresponding entry in `docs/adr/model-versions.md`.
