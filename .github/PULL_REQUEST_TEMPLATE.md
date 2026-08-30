## What does this PR do?

<!-- One or two sentences. If this touches services/risk_engine/ or services/alerting/, say exactly what changed in the logic, not just "updated risk engine". -->

## Tier of files touched

- [ ] Tier 0/1 (`services/risk_engine/`, `services/alerting/`) — see extra checklist below
- [ ] Tier 2 (`services/ingestion/`, `services/api-gateway/`, `services/gis-dashboard/`, `field-app/`)
- [ ] Tier 3 (`docs/`, `infra/` non-prod)

## Standard checklist (all PRs)

- [ ] Pre-commit hooks pass locally (`pre-commit run --all-files`)
- [ ] CI is green
- [ ] No hardcoded credentials, no real API keys, no real citizen/field PII in test fixtures
- [ ] Provenance fields (`source`, `source_timestamp`, `ingestion_timestamp`, `transformation_version`) preserved if this touches ingestion
- [ ] No new claims in code/docs/UI copy that belong on the "do not claim yet" list (see `.agents/rules/core-rules.md`)
- [ ] Docstrings added for new functions/classes (feeds the auto-doc build)

## Extra checklist — Tier 0/1 only (risk_engine / alerting)

- [ ] I re-derived the changed logic independently rather than just reading the diff (self-review while solo; ask a teammate/mentor once available)
- [ ] Any threshold, weight, or fusion formula change is called out explicitly below, not buried in the diff:

  > _describe the change here_

- [ ] Backtest results attached or linked (`tests/backtests/`) if this changes model/rule behavior
- [ ] `docs/adr/model-versions.md` updated if this is a model/threshold version change
- [ ] Left running overnight / revisited with fresh eyes before merge (solo-dev substitute for a second reviewer)

## Anything you're unsure about?

<!-- Flag it here rather than merging on a guess. -->
