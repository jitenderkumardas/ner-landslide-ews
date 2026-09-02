# Agent Handoff Document — NER Landslide EWS

**Purpose of this document:** transfer this project to a new Antigravity agent session without losing context, breaking the established workflow, or repeating decisions that have already been made. Read this entire document before touching any code.

**Repo:** `ner-landslide-ews` (public, Apache-2.0, GitHub branch protection enforced on `main`)
**Pilot corridor:** East Khasi Hills, Meghalaya — Shillong–Sohra (Cherrapunji) road corridor, 5 grid cells (`GRID-EKH-001` through `005`)
**Data status:** 100% mock/synthetic. No live IMD/GSI/ISRO API access yet. Everything is built against mock adapters by design, swappable later.

---

## 1. Master Agenda & Project Status

### Overall phase plan (from `docs/phases/`)

| Phase                                  | Status                     |
| -------------------------------------- | -------------------------- |
| Phase 1 — Planning & Feasibility       | ✅ Complete                |
| Phase 2 — Requirements Analysis        | ✅ Complete                |
| Phase 3 — System Design & Architecture | ✅ Complete                |
| **Phase 4 — Build (current)**          | 🚧 In progress — see below |
| Phase 5 — Pilot Deployment             | ⏳ Not started             |

### Phase 4 build progress — completed milestones

All of the following are **implemented, tested, committed, and merged** to `main`:

1. **Repo governance scaffold** — `.gitignore`, `README.md`, `LICENSE` (Apache-2.0), `CONTRIBUTING.md` (Conventional Commits convention), `.github/PULL_REQUEST_TEMPLATE.md`, `.agents/rules/core-rules.md` (the Antigravity agent constitution for this repo)
2. **CI/version-control baseline** — `.pre-commit-config.yaml` (ruff, prettier, gitleaks secret scanning, general hygiene hooks), `.github/workflows/pre-commit.yml`, GitHub branch protection on `main` enforced (public repo, required status check, required PR, no force-push/delete)
3. **Mock rainfall ingestion adapter** — `services/ingestion/rainfall/` — reads a CSV fixture for the pilot corridor, returns `RainfallRecord` objects with mandatory provenance fields. **9 unit tests passing.**
4. **Rainfall risk engine (first-pass, placeholder thresholds)** — `services/risk_engine/` — cumulative-rainfall-in-a-rolling-window classifier (GREEN/YELLOW/ORANGE/RED), explicitly documented as uncalibrated. **7 unit tests passing.** Backed by `docs/adr/tiering.md` and `docs/adr/model-versions.md`.
5. **API gateway** — `services/api_gateway/main.py` — FastAPI app, `/health` and `/risk-assessments` endpoints, dev-mode CORS enabled (flagged as a temporary dev setting, not production-ready). **6 unit tests passing.**
6. **GIS dashboard (static, first pass)** — `services/gis_dashboard/index.html` — Leaflet map centered on the Shillong–Sohra corridor, consumes the `/risk-assessments` API, colored severity markers, visible on-page disclaimer banner.

**Total: 22 unit tests passing** across ingestion + risk_engine + api_gateway (9 + 7 + 6).

Known naming correction already applied project-wide: the folder is `risk_engine` (underscore), not `risk-engine` (hyphen) — Python cannot import a hyphenated package name. If you see `risk-engine` referenced anywhere, that's a stale reference and should be fixed to `risk_engine`.

---

## 2. Current Step IN PROGRESS — ⚠️ NOT YET COMPLETE, NOT YET VERIFIED BY THE USER

**This is where the next agent must start.** Do not consider this done.

### What exists (written and self-tested in an isolated sandbox only — NOT yet in the user's actual repo)

A synthetic-data backtest harness for the rainfall risk engine, at `tests/backtests/`:

- `harness.py` — core logic: `LandslideEvent`, `BacktestResult`, `EpisodeResult` dataclasses; `find_first_warning()` with **explicit no-lookahead enforcement** (a real historical-backtesting correctness requirement — a prediction must never see data timestamped at or after the moment being evaluated); `evaluate_event()`, `evaluate_no_event_episode()`, `run_full_backtest()`
- `config.py` — `BACKTEST_CONFIG` with two explicit, documented-as-unvalidated assumptions: `event_tolerance_hours: 24` and `minimum_warning_level: Severity.ORANGE`
- `metrics.py` — confusion matrix, precision/recall/F1/false-positive-rate/false-negative-rate/lead-time statistics, with a **sample-size disclaimer baked into the returned data itself**, not just a comment
- `run_backtest.py` — CLI entry point (`python -m tests.backtests.run_backtest`) that writes `reports/backtest/baseline_metrics.json`, `event_results.csv`, and `summary.md`
- `test_backtest_harness.py` — 13 tests, including two that specifically try to break the no-lookahead guarantee (a huge rainfall spike placed exactly at/after the cutoff must NOT trigger a warning)
- `fixtures/historical_landslides.csv` — 4 synthetic landslide events
- `fixtures/rainfall_hourly.csv` — 164 rows of synthetic hourly rainfall across 6 grid cells
- `fixtures/generate_backtest_fixtures.py` — the generator script presumed to have produced the two CSVs above

**Sandbox verification performed:** `pytest tests/backtests/ -v` → 13/13 passed. `python -m tests.backtests.run_backtest` → ran successfully, produced a correctly-formatted `summary.md` with confusion matrix (TP=3, FN=1, FP=1, TN=1), precision/recall 0.75, average lead time 6.33 hours — all clearly labeled as synthetic and non-authoritative.

### What is explicitly NOT done — the next agent's task list

1. **Not delivered to the actual project repository yet.** These files exist only in an isolated verification sandbox. They must be placed into the real repo at the paths listed above.
2. **Not committed, not pushed, no PR opened.**
3. **Cleanup required before commit:** an earlier abandoned draft attempt left two unused, non-referenced files — `tests/backtests/fixtures/synthetic_events.csv` and `synthetic_event_rainfall.csv`. These have already been deleted in the verification sandbox but **may still exist in the user's local working copy** if any earlier draft was copied over. Confirm they are not present before committing; if they are, delete them — they are dead code that would confuse anyone reading the fixtures folder.
4. **`generate_backtest_fixtures.py` has not been independently re-run and diffed against the committed CSVs** to confirm there's no drift between the generator and the fixture files it supposedly produced. Run it and confirm the output matches what's committed, or reconcile if not.
5. **No `docs/adr/model-versions.md` entry has been added** documenting this backtest run. Per this repo's own rule (see section 4 below), every validation run against `risk_engine` should be logged, append-only.
6. **No decision recorded on whether `reports/backtest/` generated output should be committed to git or gitignored.** Recommendation: gitignore it (it's regenerable from `run_backtest.py`), but this must be an explicit decision, added to `.gitignore`, not an oversight.
7. **The two config assumptions in `config.py` (`event_tolerance_hours=24`, `minimum_warning_level=ORANGE`) have not been explicitly signed off by the user.** They are clearly commented as prototype assumptions, but per the tiering rules this touches Tier 0/1-adjacent validation logic and deserves a real look before merge.
8. **`docs/adr/tiering.md` does not yet list `tests/backtests/` in its tier table.** It should be added — almost certainly Tier 2 (it's read-only validation code that calls but never modifies `risk_engine`), but this needs to be a recorded decision, not an assumption.
9. **No pre-commit / CI run has been performed on these files in the real repo** — ruff/prettier formatting has not touched them yet, and they have not been through the actual GitHub Actions check.

---

## 3. Repository Architecture & Directory Structure

```
ner-landslide-ews/
├── .agents/rules/core-rules.md          # Antigravity agent constitution — READ FIRST
├── .github/
│   ├── workflows/pre-commit.yml         # CI: runs pre-commit hooks on push/PR
│   └── PULL_REQUEST_TEMPLATE.md         # Tiered review checklist
├── .gitignore
├── .pre-commit-config.yaml
├── .env.example                         # all data-source keys blank; USE_MOCK_ADAPTERS=true
├── LICENSE                              # Apache-2.0
├── README.md
├── CONTRIBUTING.md                      # Conventional Commits convention
├── requirements.txt
├── docs/
│   ├── phases/                          # Phase 1-3 planning docs (canonical source)
│   └── adr/
│       ├── tiering.md                   # risk tier table — needs tests/backtests/ added
│       └── model-versions.md            # append-only log — needs backtest entry added
├── services/
│   ├── ingestion/rainfall/
│   │   ├── base.py                      # RainfallAdapter interface, RainfallRecord model
│   │   ├── mock_adapter.py              # reads fixtures/mock_rainfall_hourly.csv
│   │   ├── real_adapter.py              # stub — raises clear error, no fake IMD schema
│   │   ├── __init__.py                  # factory: get_rainfall_adapter() switches mock/real
│   │   └── fixtures/mock_rainfall_hourly.csv
│   ├── risk_engine/                     # NOTE: underscore, not hyphen
│   │   ├── severity.py                  # Severity enum GREEN<YELLOW<ORANGE<RED
│   │   ├── thresholds.py                # ThresholdSet — PLACEHOLDER values, v0.1
│   │   ├── models.py                    # RiskAssessment output dataclass
│   │   ├── rainfall_risk.py             # calculate_rainfall_risk() — the core function
│   │   └── __init__.py
│   ├── api_gateway/
│   │   └── main.py                      # FastAPI: GET /health, GET /risk-assessments
│   └── gis_dashboard/
│       └── index.html                   # Leaflet map, consumes /risk-assessments
├── tests/
│   ├── ingestion/test_rainfall_adapter.py     (9 tests)
│   ├── risk_engine/test_rainfall_risk.py      (7 tests)
│   ├── api_gateway/test_main.py               (6 tests)
│   └── backtests/                       # ⚠️ SEE SECTION 2 — IN PROGRESS
│       ├── harness.py
│       ├── config.py
│       ├── metrics.py
│       ├── run_backtest.py
│       ├── test_backtest_harness.py     (13 tests, sandbox-verified only)
│       └── fixtures/
│           ├── historical_landslides.csv
│           ├── rainfall_hourly.csv
│           └── generate_backtest_fixtures.py
└── reports/backtest/                    # generated by run_backtest.py — gitignore decision pending
```

### Data/control flow

```
CSV fixture → MockRainfallAdapter.fetch_range()/fetch_latest()
            → List[RainfallRecord] (with provenance fields)
            → calculate_rainfall_risk() → List[RiskAssessment]
            → FastAPI /risk-assessments → JSON (with disclaimer)
            → Leaflet dashboard fetch() → colored map markers

Backtest harness (parallel, read-only path):
historical_landslides.csv + rainfall_hourly.csv
            → harness.run_full_backtest()
            → calls the SAME calculate_rainfall_risk() (never modifies it)
            → metrics.compute_metrics()
            → run_backtest.py writes reports/backtest/*
```

---

## 4. SDLC & Governance Rules (from `.agents/rules/core-rules.md` — read the full file)

- **Risk tiering:** `services/risk_engine/` and `services/alerting/` (not yet built) are Tier 0/1 — any threshold/weight/logic change must be called out explicitly in the PR, never buried in a diff. Everything else in `services/` is Tier 2 — standard single-review flow. `tests/backtests/` tiering is an open item (see section 2, point 8).
- **Pre-pilot mock data disclaimer is mandatory, not optional cosmetic text.** It must appear in: every API response from `/risk-assessments` (already implemented), and visibly on the GIS dashboard UI itself (already implemented as a banner). Any new user-facing surface (a future field-app screen, a future alert message) must carry the same disclaimer until real validated data/thresholds exist.
- **No-lookahead / leakage prevention** (a rule that emerged from building the backtest harness and should now be treated as a standing rule for all future validation code): any code that evaluates historical or backtest data must never allow the risk engine to see data timestamped at or after the moment being evaluated. `harness.py`'s `_records_up_to()` / `find_first_warning()` is the reference implementation and enforcement pattern — reuse this approach for any future backtest or replay logic, don't reinvent it.
- **Provenance fields are mandatory** on every ingested record: `source`, `source_timestamp`, `ingestion_timestamp`, `transformation_version`.
- **"Do not claim yet" list:** no specific accuracy/precision numbers outside a logged backtest entry; no "real-time" claims without measured latency; no "covers all of NER" — always name the pilot corridor specifically; no implication that the system is validated for live emergency use.
- **Tier 2 review guideline (solo-dev in effect):** standard PR, pre-commit + CI must pass, one round of self-review. **Tier 0/1 review guideline:** do not merge in the same session the code was written — come back after a break and re-read the diff as if reviewing someone else's work before merging. This applies to the backtest harness's interaction with `risk_engine` logic even though the harness folder itself is likely Tier 2 — because it validates Tier 0/1 code, treat its merge with the same "wait before merging" discipline.
- **Dependency hygiene:** never add a package without confirming the name/version actually resolves — hallucinated or typosquatted package names are a known agent failure mode.
- **Every function/class needs a docstring** sufficient for the (not-yet-built) auto-doc pipeline.
- **When unsure, stop and ask** rather than proceeding on the most plausible-sounding assumption — this applies especially to the two config assumptions flagged in section 2, point 7.

---

## 5. Immediate Prompt for Next Agent

Copy-paste this directly into the new Antigravity agent session:

```
Read docs/handoff/agent-handoff-backtest-harness.md in full before doing anything else.

Your task: finish and land the backtest harness that's described as "in progress" in
section 2 of that document. Specifically, in order:

1. Verify the files listed in section 2 exist at the correct paths in THIS repo
   (tests/backtests/harness.py, config.py, metrics.py, run_backtest.py,
   test_backtest_harness.py, fixtures/historical_landslides.csv, fixtures/rainfall_hourly.csv,
   fixtures/generate_backtest_fixtures.py). If any are missing, flag it — do not
   fabricate replacements from memory; ask for them to be re-supplied.

2. Confirm there are NO leftover files named synthetic_events.csv or
   synthetic_event_rainfall.csv in tests/backtests/fixtures/. Delete them if present —
   they are dead code from an abandoned earlier draft.

3. Run `pytest tests/backtests/ -v` and confirm all 13 tests pass in this repo's
   actual environment, not just report that they should.

4. Run `python -m tests.backtests.run_backtest` and inspect reports/backtest/summary.md
   for correctness — confirm the synthetic-data disclaimer is present and prominent.

5. Re-run fixtures/generate_backtest_fixtures.py and confirm it reproduces
   historical_landslides.csv and rainfall_hourly.csv exactly (no drift). Reconcile if not.

6. Add a decision to .gitignore for reports/backtest/ (recommended: ignore it, since
   it's regenerable) — state the decision explicitly in the PR description, don't
   just silently add the line.

7. Add an entry to docs/adr/model-versions.md documenting this backtest run: date,
   data source (synthetic_fixture), confusion matrix, metrics, and the explicit
   statement that this validates harness correctness, not real-world model performance.

8. Add tests/backtests/ to the tier table in docs/adr/tiering.md (propose Tier 2,
   but flag for human confirmation since it validates Tier 0/1 code).

9. Explicitly surface the two config.py assumptions (event_tolerance_hours=24,
   minimum_warning_level=ORANGE) in the PR description for human sign-off — do not
   silently treat them as final.

10. Run pre-commit on all touched files, open a PR following the standard template,
    and do NOT merge until CI is green AND a human has reviewed the config
    assumptions from step 9.

Do not modify services/risk_engine/ as part of this task — the harness must only
call the existing calculate_rainfall_risk(), never change it.
```

Save this handoff document itself at `docs/handoff/agent-handoff-backtest-harness.md` in the repo so the prompt above's file reference resolves correctly.
