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
