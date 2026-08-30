---
trigger: always_on
---

# Antigravity Agent Rules — NER Landslide EWS

These rules apply to every agent task in this repository. Read this before generating, editing, or reviewing any code here.

## 1. Project context (don't re-derive this from the code — it's already decided)

This is an AI-based early warning and landslide risk monitoring system for India's North Eastern Region. Its outputs (risk scores, alerts) can inform real evacuation and emergency-response decisions once it reaches pilot/production. **We are currently pre-pilot, building against mocked data sources.** Do not write code, comments, or docs that imply live alerting is active.

## 2. Risk tiering — this determines how carefully you must work in each folder

| Path                                                                                    | Tier     | Rule                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/risk_engine/`                                                                 | Tier 0/1 | Never merge without flagging for 2-reviewer sign-off. Never silently change a threshold, weight, or fusion formula — call it out explicitly in the PR description.                              |
| `services/alerting/`                                                                    | Tier 0/1 | Same as above. Alert severity mapping and CAP object generation must match `docs/adr/alert-policy.md` exactly — if that file doesn't exist yet, stop and ask rather than inventing the mapping. |
| `services/ingestion/`, `services/api-gateway/`, `services/gis-dashboard/`, `field-app/` | Tier 2   | Standard 1-reviewer PR flow. Still must preserve provenance fields (rule 4).                                                                                                                    |
| `docs/`, `infra/` non-prod configs                                                      | Tier 3   | Normal speed, lighter review.                                                                                                                                                                   |

## 3. Data source honesty

- We do not currently have live API access to IMD, GSI, ISRO/Bhuvan, or apisetu.gov.in. Every ingestion adapter must be built against a documented mock interface (`services/ingestion/*/mock_adapter.py` or equivalent), with the real-adapter class stubbed but clearly marked `# TODO: real API — not yet authorized`.
- Never fabricate a plausible-looking API response schema and present it as if it came from real documentation. If you don't have the real IMD/GSI/ISRO schema, say so and propose a reasonable mock schema explicitly labeled as an assumption.
- Never hardcode a real-looking API key, token, or credential — not even as a "placeholder." Use `os.environ["IMD_API_KEY"]` style references pointing at `.env.example`.

## 4. Provenance — every ingested record needs these fields, no exceptions

```
source              # e.g. "IMD_mock", "GSI_historical"
source_timestamp    # when the source says this data is from
ingestion_timestamp # when we pulled it
transformation_version  # version tag of whatever pipeline touched it
```

If you write an ingestion adapter that doesn't carry these through, that's a bug — fix it before marking the task done, don't wait for review to catch it.

## 5. Model versioning — required for anything in `risk_engine/`

Every trained model artifact or rule-based threshold change must log: model/version id, dataset version used, evaluation metrics (recall, precision, PR-AUC, lead time — not just accuracy), calibration notes, and threshold value. Write this to `docs/adr/model-versions.md` as an append-only log, one entry per change.

## 6. Language and claims discipline — "do not claim yet" list

Do not write, in code comments, docstrings, UI copy, README, or generated docs, any of the following until they are actually validated and a human has signed off:

- Specific accuracy/precision numbers (e.g. ">85% accuracy") unless pulled directly from a logged backtest result in `docs/adr/model-versions.md`
- "Real-time" unless the actual measured latency has been tested and logged
- "Covers all of NER" or similar full-coverage claims during pilot phase — say "pilot corridor" or name the specific district/route instead
- Any claim that the system is validated for live emergency use

If you're drafting UI copy or a report and need a placeholder number, write `[TBD — needs backtest]` rather than inventing a plausible-sounding figure.

## 7. Diff size and task scope

Keep generated diffs small enough for a human to read line-by-line in under 30 minutes. If a task naturally produces a larger change, stop and propose splitting it into sequential PRs instead of submitting one large diff.

## 8. What you must never do in this repo

- Never commit anything to `.env`, real credentials, or citizen/field-report PII test fixtures — use synthetic data.
- Never modify branch protection, CI required-checks, or repository settings.
- Never add a dependency without confirming the package name and latest version actually resolve (agents have a known failure mode of hallucinating package names) — if you can't verify it, flag it rather than guessing.
- Never merge your own PR. Every task ends in an open PR for human review, tagged with the tier from section 2.

## 9. Documentation as you go

Every function/class you write in `services/` or `field-app/` needs a docstring sufficient for the auto-doc generator (MkDocs + mkdocstrings) to produce something useful — don't leave this for a "docs pass later."

## 10. When you're unsure

If a task requires a decision this file doesn't cover (a new trust boundary, a new external dependency, an ambiguous requirement from `docs/phases/`), stop and ask rather than making the most plausible-sounding assumption and proceeding.
