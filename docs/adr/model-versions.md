# Model / Threshold Version Log

Append-only. One entry per change to any rule, threshold, weight, or trained model in `services/risk_engine/`. Never edit or delete a past entry — add a new one that supersedes it.

---

## rainfall-threshold-v0.1-placeholder

- **Date:** 2026-08 (pilot phase)
- **Type:** Rule-based threshold (not a trained model)
- **What it does:** Classifies grid-cell severity (GREEN/YELLOW/ORANGE/RED) from cumulative rainfall in a trailing 3-hour window.
- **Thresholds:** yellow ≥ 15mm, orange ≥ 25mm, red ≥ 40mm (per 3-hour window)
- **Dataset used for calibration:** **None.** These are round-number starting guesses for a high-rainfall NER hill district, explicitly not derived from historical GSI landslide events.
- **Metrics:** N/A — not yet backtested. Do not cite an accuracy/precision/recall figure for this version anywhere.
- **Known limitations:** Rainfall-only signal. Does not yet incorporate soil moisture, slope/susceptibility mapping, or antecedent-rainfall decay (all in the Phase 3 fusion design as separate inputs, not yet built).
- **Status:** Placeholder — must be superseded by a calibrated version, validated against `tests/backtests/` using real or GSI-sourced historical landslide events, before any live/pilot alert is enabled.
- **Code reference:** `services/risk_engine/thresholds.py`, `THRESHOLD_VERSION = "rainfall-threshold-v0.1-placeholder"`

---

## backtest-harness-run-001 — synthetic fixture validation

- **Date:** 2026-09-02
- **Type:** Backtest harness correctness run (NOT a model-training or calibration run)
- **Threshold version tested:** `rainfall-threshold-v0.1-placeholder`
- **Dataset:** `tests/backtests/fixtures/historical_landslides.csv` + `tests/backtests/fixtures/rainfall_hourly.csv`
  — 4 synthetic events across 4 grid cells, 2 no-event episodes. **ALL DATA IS SYNTHETIC/MOCK.**
- **Confusion matrix (episode-level):** TP=3 · FN=1 · FP=1 · TN=1
- **Metrics (on 4-event synthetic sample — not statistically meaningful):**
  - Precision: [TBD — needs real backtest] / Recall: [TBD — needs real backtest]
    _(Synthetic values: P=0.75, R=0.75, F1=0.75, FPR=0.5, FNR=0.25 — cited here only to document harness output, NOT as performance claims)_
  - Average lead time (TPs only): 6.33 h · Median: 6.0 h · Minimum: 2.0 h
- **What this validates:** That `tests/backtests/harness.py` correctly enforces no-lookahead evaluation, computes lead-time arithmetic accurately, classifies episodes as TP/FP/TN/FN, and that `tests/backtests/metrics.py` handles zero-denominator edge cases without raising exceptions. The 13-test suite covers these properties explicitly, including two tests that deliberately inject a rainfall spike at/after the evaluation cutoff to confirm it is invisible to the prediction.
- **What this does NOT validate:** Real-world recall or precision of `rainfall-threshold-v0.1-placeholder` against historical NER landslide events. No real GSI/IMD event data has been used. Do not cite any figure from this entry as a model-accuracy claim.
- **Known model blind spot documented:** BTEST-003 (GRID-EKH-001) is a synthetic landslide with no preceding rainfall signal — the model misses it by design. This documents why a rainfall-only baseline is insufficient and why Phase 3 calls for soil moisture, susceptibility, and satellite fusion inputs.
- **Config prototype assumptions (require sign-off before live use):**
  - `event_tolerance_hours: 24` — round-number placeholder; not derived from NER logistics or evacuation-time study. Accepted by user 2026-09-02 as prototype-only.
  - `minimum_warning_level: Severity.ORANGE` — ORANGE is the first actionable tier per `severity.py` definitions. Accepted by user 2026-09-02 as prototype-only. Must be revisited when `docs/adr/alert-policy.md` is defined.
- **Status:** Harness correctness validated on synthetic fixture. Threshold performance NOT validated. Do not cite metrics above as model accuracy.
- **Code reference:** `tests/backtests/`, `services/risk_engine/thresholds.py`
