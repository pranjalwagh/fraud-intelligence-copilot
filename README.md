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

The dataset's own fraud flag misses 99.8% of fraud. A single explainable rule — the transaction fully drains the sender's account balance — catches 97.6% of it with zero false positives. These numbers are independently verifiable via the `PRECISION`, `RECALL`, and `BASELINE_FLAGGED_TRANSACTIONS` metrics on the `FRAUD_SEMANTIC` semantic view (or just ask the copilot "what's the precision and recall of the risk score rule?").

## Architecture

1. **Ingestion** — PaySim CSV → `FRAUD_HACKATHON.RAW.PAYSIM` (6.36M rows)
2. **Rule layer** — governed view `FRAUD_FLAGS` computes a `RISK_SCORE` from balance-drain and overnight-window signals
3. **Semantic layer** — `FRAUD_SEMANTIC` semantic view exposes consistent, governed definitions for natural-language querying
4. **NL interface** — Cortex Analyst (native + a custom-branded Streamlit chat app) answers plain-English questions with the answer *and* the generated SQL
5. **Audit layer** — `SNOWFLAKE.CORTEX.COMPLETE`, using a GA Cortex model chosen dynamically at runtime (see the app's model picker — never hardcoded), turns any flagged transaction into a formal suspicious-activity narrative with cited risk indicators and a recommended action

## Setup & Run

1. Run the SQL scripts in order (each is idempotent):
   - `sql/01_setup_database.sql` — database, schema, warehouse
   - `sql/02_create_paysim_table.sql` — `PAYSIM` table + load stage
   - `sql/03_create_fraud_flags_view.sql` — `FRAUD_FLAGS` rule view
   - `sql/06_create_chat_history_table.sql` — chat history table
   - `sql/07_create_voice_input_stage.sql` — voice upload stage
   - `sql/08_create_document_input_stage.sql` — document upload stage
   - `sql/09_grants_template.sql` — optional, only if granting access to a role other than the owner
   - `sql/10_cleanup_anonymous_history.sql` — optional maintenance script; deletes old anonymous-viewer chat history
2. Download the PaySim CSV (Kaggle, `PS_20174392719_1491204439457_log.csv`), place it at the repo root, then run `sql/02_create_paysim_table.sql` if you haven't already (creates the target table and stage the loader needs — see the docstring at the top of `scripts/load_paysim_data.py` for full prerequisites). Install the loader's dependencies with `pip install -r scripts/requirements.txt` (requires Python 3.11+ for the standard-library `tomllib` module), then run it — `py scripts/load_paysim_data.py` on Windows, or `python3 scripts/load_paysim_data.py` on macOS/Linux.
3. Deploy the semantic view: `cortex agent-studio sv-deploy --file-path cortex_project/FRAUD_SEMANTIC.sv.yaml --fqn FRAUD_HACKATHON.RAW.FRAUD_SEMANTIC` (see `sql/04_deploy_semantic_view.sql`).
4. Deploy the Streamlit app following `sql/05_deploy_streamlit_app.sql` — upload `streamlit_app/*` to the stage, then `CREATE OR REPLACE STREAMLIT` + `ALTER STREAMLIT ... ADD LIVE VERSION FROM LAST`. Repeat this step after any app code change (files only copy in at `CREATE` time).

## Repo Contents

- `streamlit_app/fraud_copilot_streamlit_app.py` — the deployed chat app (multi-page: chat, risk overview, audit reports; NL chat via Cortex Analyst with voice input and document Q&A; audit report generator)
- `streamlit_app/environment.yml` — package pins for the app's warehouse runtime
- `sql/01_setup_database.sql` … `sql/10_cleanup_anonymous_history.sql` — numbered setup/deploy/maintenance scripts (see Setup & Run above)
- `scripts/load_paysim_data.py` — PaySim CSV loader
- `scripts/requirements.txt` — loader's Python dependencies
- `cortex_project/FRAUD_SEMANTIC.sv.yaml` — the governed semantic view definition
- `cortex_project/cortex-project.yaml` — Cortex project config for `sv-deploy`

## Key Insight

Fraud in this dataset is confined entirely to `TRANSFER` and `CASH_OUT` transactions, and 97.8% of fraud cases drain the origin account's balance to exactly zero — a strong, explainable signal. That 97.8% is a descriptive stat about the raw data (any fraud row ending at a zero balance); the 97.6% recall figure above is the deployed rule's actual catch rate, which also requires the correct transaction type and a non-trivial starting balance — so the two numbers measure different things and aren't expected to match exactly. Either way, a single explainable rule captures almost all of it with zero false positives, while remaining fully auditable for a regulated use case.

## Built With

Snowflake CoCo CLI · Snowflake Cortex Analyst · Snowflake Cortex Complete (GA model chosen dynamically) · Snowflake Semantic Views · Streamlit in Snowflake

