# AI-Based Early Warning and Landslide Risk Monitoring System — NER

Building a safer, climate-resilient North East through intelligence, data, and early action.

> ⚠️ **Status: Pre-pilot / MVP development.** Not connected to live alerting. Do not use outputs of this repository for real evacuation or emergency-response decisions until Phase 4–5 validation (see `docs/phases/`) is complete and signed off.

## Purpose

Assess the need, feasibility, and viability of — and then build — an AI-enabled early warning and landslide risk monitoring system for the North Eastern Region (NER), covering multi-source data ingestion, AI/ML risk prediction, real-time alerting, GIS-based visualization, and offline-capable field reporting.

## Project status

| Phase                                       | Status         |
| ------------------------------------------- | -------------- |
| Phase 1 — Planning & Feasibility            | ✅ Complete    |
| Phase 2 — Requirements Analysis             | ✅ Complete    |
| Phase 3 — System Design & Architecture      | ✅ Complete    |
| Phase 4 — ML Model Development & Validation | 🚧 In progress |
| Phase 5 — Pilot Deployment                  | ⏳ Not started |

Full planning documents: [`docs/phases/`](./docs/phases)

## Repository structure

```
services/ingestion/      # IMD / GSI / ISRO / field-report adapters
services/risk_engine/    # susceptibility + trigger + fusion (Tier 0/1 — 2-reviewer required)
services/alerting/       # CAP alert generation + channel delivery (Tier 0/1 — 2-reviewer required)
services/api-gateway/
services/gis-dashboard/
field-app/               # offline-first field reporting app
infra/                   # Docker / IaC
tests/backtests/         # historical-event validation for the risk engine
docs/adr/                # architecture decision records
docs/agent-logs/         # AI-agent task artifacts, kept for audit trail
```

## Data sources (current)

Building against **mocked adapters** first; no live API access yet. Target sources: IMD (weather), GSI (geological/historical landslide data), ISRO/Bhuvan (satellite, DEM, soil moisture), state PWD/BRO (road & infrastructure), [apisetu.gov.in](https://apisetu.gov.in) (candidate for other government data feeds), and citizen/field-officer reports.

## Contributing / working practices

This project follows a tiered review process — see `docs/adr/tiering.md`. In short: dashboard and field-app changes need one reviewer; anything touching `risk_engine/` or `alerting/` needs two, with independent re-derivation of the logic, not just a read-through. See `.agents\rules\core-rules.md` for the agent-assisted development constraints in force for this repo.

## License

Apache-2.0 — see [LICENSE](./LICENSE).
