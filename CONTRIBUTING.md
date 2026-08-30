# Contributing / Working Practices

## Commit message format — Conventional Commits

Every commit follows: `<type>(<scope>): <short description>`

**Types:**

| Type       | Use for                                |
| ---------- | -------------------------------------- |
| `feat`     | a new capability                       |
| `fix`      | a bug fix                              |
| `docs`     | documentation only                     |
| `style`    | formatting, no logic change            |
| `refactor` | code restructuring, no behavior change |
| `perf`     | performance improvement                |
| `test`     | adding/fixing tests                    |
| `chore`    | tooling, config, dependencies          |
| `ci`       | CI/CD workflow changes                 |
| `build`    | build system / packaging               |
| `revert`   | reverting a previous commit            |

**Scopes** (match the folder you're touching):
`ingestion`, `risk-engine`, `alerting`, `api-gateway`, `gis-dashboard`, `field-app`, `infra`, `docs`, `agents` (for `.agents/` rules changes)

**Examples:**

```
feat(ingestion): add mock adapter for IMD rainfall data
fix(risk-engine): correct soil-moisture normalization bug
docs(phases): add Phase 4 ML validation plan
chore: add pre-commit hooks and CI workflow
risk-engine(threshold): raise rainfall trigger to 150mm/24h — see PR #12 for backtest
```

Why this matters here specifically: commit history for `risk-engine` and `alerting` is your audit trail if this system's decisions are ever questioned. A vague `"updated stuff"` commit on those paths is not acceptable — say what changed and why.

## Branching

- `main` is protected — no direct pushes, everything goes through a PR.
- Branch names: `<type>/<short-description>`, e.g. `feat/mock-imd-adapter`, `fix/risk-threshold-bug`.

## Pull requests

- Fill out the PR template fully — especially the Tier 0/1 extra checklist if you touched `risk-engine/` or `alerting/`.
- While solo: don't merge a Tier 0/1 PR the same session you wrote it. Come back after a break, re-read the diff as if reviewing someone else's code, then merge.
- Once teammates join: Tier 0/1 PRs require an actual second person's review before merge — update branch protection settings at that point (see `docs/adr/tiering.md`).

## Local setup

```bash
pip install pre-commit --break-system-packages   # or without the flag in a venv
pre-commit install
pre-commit run --all-files   # sanity check before your first commit
```
