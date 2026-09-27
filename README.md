# 🛡️ Risk & Fraud Intelligence Copilot

**Snowflake CoCo CLI Hackathon 2026 – GCC Edition** | Problem Statement 1: Risk, Fraud and Regulatory Intelligence Copilot

A natural-language copilot that flags suspicious transactions using transparent, explainable rules and answers plain-English questions with audit-ready output — built end-to-end with Snowflake CoCo CLI.

**🔗 [Live App](https://app.snowflake.com/PZLLABX-RS49195/#/streamlit-apps/FRAUD_HACKATHON.RAW.FRAUD_COPILOT)**

---

## The Problem

Banking and NBFC teams manage real-time fraud, liquidity/credit risk, and regulatory reporting (AML, Basel) largely by hand. Investigators sift transaction logs manually, and audit trails get written up after the fact rather than generated alongside detection.

## The Result

| Metric | Value |
| --- | --- |
| Dataset | PaySim — 6,362,620 synthetic transactions, 8,213 fraud (0.13%) |
| Baseline (`ISFLAGGEDFRAUD`) recall | **0.2%** (16 of 8,213 caught) |
| This copilot's recall | **97.6%** (8,018 of 8,213 caught) |
| Precision | **100%** (zero false positives) |

The dataset's own fraud flag misses 99.8% of fraud. A single explainable rule — the transaction fully drains the sender's account balance — catches 97.6% of it with zero false positives.

## Architecture

1. **Ingestion** — PaySim CSV → `FRAUD_HACKATHON.RAW.PAYSIM` (6.36M rows)
2. **Rule layer** — governed view `FRAUD_FLAGS` computes a `RISK_SCORE` from balance-drain and overnight-window signals
3. **Semantic layer** — `FRAUD_SEMANTIC` semantic view exposes consistent, governed definitions for natural-language querying
4. **NL interface** — Cortex Analyst (native + a custom-branded Streamlit chat app) answers plain-English questions with the answer *and* the generated SQL
5. **Audit layer** — `SNOWFLAKE.CORTEX.COMPLETE` (Claude Sonnet 4.5) turns any flagged transaction into a formal suspicious-activity narrative with cited risk indicators and a recommended action

## Repo Contents

- `streamlit/fraud_copilot_streamlit_app.py` — the deployed chat app (metrics, NL chat via Cortex Analyst, before/after chart, audit report generator)
- `sql/fraud_flags_view.sql` — the rule-based flagging view
- `sql/fraud_semantic_view.sql` — the governed semantic view definition

## Key Insight

Fraud in this dataset is confined entirely to `TRANSFER` and `CASH_OUT` transactions, and 97.8% of fraud cases drain the origin account's balance to exactly zero — a strong, explainable signal that a simple rule captures almost as well as a trained model would, while remaining fully auditable for a regulated use case.

## Built With

Snowflake CoCo CLI · Snowflake Cortex Analyst · Snowflake Cortex Complete (Claude Sonnet 4.5) · Snowflake Semantic Views · Streamlit in Snowflake
