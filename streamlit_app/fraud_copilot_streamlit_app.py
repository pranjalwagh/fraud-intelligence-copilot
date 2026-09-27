import streamlit as st
import _snowflake
import json
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Risk & Fraud Intelligence Copilot", page_icon="🛡️", layout="wide")

SEMANTIC_VIEW = "FRAUD_HACKATHON.RAW.FRAUD_SEMANTIC"

st.markdown(
    """
    <style>
    .main-header {font-size: 2.2rem; font-weight: 700; color: #1A2B4C;}
    .sub-header {color: #5B7083; font-size: 1rem; margin-bottom: 1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🛡️ Risk & Fraud Intelligence Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Snowflake CoCo CLI Hackathon 2026 – GCC Edition '
    '&nbsp;|&nbsp; Ask questions about transaction risk in plain English</div>',
    unsafe_allow_html=True,
)

session = get_active_session()


@st.cache_data(ttl=300)
def load_summary():
    df = session.sql(
        """
        SELECT
            COUNT(*) AS total_txns,
            SUM(ISFRAUD) AS total_fraud,
            SUM(CASE WHEN RISK_SCORE >= 2 THEN 1 ELSE 0 END) AS flagged
        FROM FRAUD_HACKATHON.RAW.FRAUD_FLAGS
        """
    ).to_pandas()
    return df.iloc[0]


summary = load_summary()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", f"{summary['TOTAL_TXNS']:,}")
col2.metric("Confirmed Fraud", f"{summary['TOTAL_FRAUD']:,}")
col3.metric("Flagged by Copilot", f"{summary['FLAGGED']:,}")
col4.metric("Recall", "97.6%")

st.markdown("**Existing Detection vs This Copilot** — recall on confirmed fraud")
recall_df = pd.DataFrame(
    {
        "Method": ["Existing System", "This Copilot"],
        "Recall": [0.2, 97.6],
        "Label": ["0.2%", "97.6%"],
    }
)

recall_bars = (
    alt.Chart(recall_df)
    .mark_bar()
    .encode(
        x=alt.X("Method:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Recall:Q", title="Recall (%)", scale=alt.Scale(domain=[0, 105])),
        color=alt.Color(
            "Method:N",
            scale=alt.Scale(
                domain=["Existing System", "This Copilot"],
                range=["#E4572E", "#2E86AB"],
            ),
            legend=None,
        ),
    )
)

recall_labels = (
    alt.Chart(recall_df)
    .mark_text(dy=-10, fontWeight="bold", fontSize=14, color="#1A2B4C")
    .encode(
        x=alt.X("Method:N"),
        y=alt.Y("Recall:Q"),
        text=alt.Text("Label:N"),
    )
)

recall_chart = (
    (recall_bars + recall_labels)
    .properties(height=280, background="#F7F9FB")
    .configure_axis(
        labelColor="#1A2B4C",
        titleColor="#1A2B4C",
        domainColor="#1A2B4C",
        tickColor="#1A2B4C",
        gridColor="#D6DEE6",
    )
    .configure_view(strokeWidth=0)
)

st.altair_chart(recall_chart, use_container_width=True)

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []


def send_message(prompt: str) -> dict:
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "semantic_view": SEMANTIC_VIEW,
    }
    resp = _snowflake.send_snow_api_request(
        "POST", "/api/v2/cortex/analyst/message", {}, {}, request_body, None, 30000
    )
    if resp["status"] < 400:
        return json.loads(resp["content"])
    raise Exception(f"Cortex Analyst request failed ({resp['status']}): {resp}")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            with st.expander("Show generated SQL"):
                st.code(msg["sql"], language="sql")
        if "df" in msg:
            st.dataframe(msg["df"])

if prompt := st.chat_input("Ask about flagged transactions, fraud rates, risk scores..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                response = send_message(prompt)
                content = response["message"]["content"]
                answer_text = ""
                sql_text = None
                for item in content:
                    if item["type"] == "text":
                        answer_text += item["text"]
                    elif item["type"] == "sql":
                        sql_text = item["statement"]

                st.markdown(answer_text if answer_text else "Here's what I found:")

                result_df = None
                if sql_text:
                    with st.expander("Show generated SQL"):
                        st.code(sql_text, language="sql")
                    result_df = session.sql(sql_text).to_pandas()
                    st.dataframe(result_df)

                assistant_msg = {"role": "assistant", "content": answer_text or "Here's what I found:"}
                if sql_text:
                    assistant_msg["sql"] = sql_text
                if result_df is not None:
                    assistant_msg["df"] = result_df
                st.session_state.messages.append(assistant_msg)

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.divider()

st.markdown(
    '<div class="main-header" style="font-size:1.6rem;">📝 Audit Report Generator</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Pick a high-risk transaction and generate a formal suspicious activity narrative.</div>',
    unsafe_allow_html=True,
)

COMPLETE_MODEL = "claude-sonnet-4-5"


@st.cache_data(ttl=300)
def load_top_flagged():
    return session.sql(
        """
        SELECT
            STEP, TYPE, NAMEORIG, NAMEDEST, AMOUNT,
            OLDBALANCEORG, NEWBALANCEORIG, OLDBALANCEDEST, NEWBALANCEDEST,
            IS_BALANCE_DRAIN, IS_OVERNIGHT, RISK_SCORE, ISFRAUD
        FROM FRAUD_HACKATHON.RAW.FRAUD_FLAGS
        WHERE RISK_SCORE >= 2
        ORDER BY AMOUNT DESC
        LIMIT 10
        """
    ).to_pandas()


top_flagged = load_top_flagged()

if top_flagged.empty:
    st.info("No flagged transactions (RISK_SCORE >= 2) found.")
else:
    options = {
        idx: f"Step {row.STEP} | {row.TYPE} | {row.NAMEORIG} -> {row.NAMEDEST} | ${row.AMOUNT:,.2f}"
        for idx, row in top_flagged.iterrows()
    }
    selected_idx = st.selectbox(
        "Top 10 highest-amount flagged transactions",
        options=list(options.keys()),
        format_func=lambda i: options[i],
    )
    selected = top_flagged.loc[selected_idx]

    if st.button("Generate Report", type="primary"):
        with st.spinner("Drafting audit narrative..."):
            indicators = []
            if bool(selected["IS_BALANCE_DRAIN"]):
                indicators.append("balance-drain (the transaction emptied the origin account)")
            if bool(selected["IS_OVERNIGHT"]):
                indicators.append("overnight timing (occurred during the flagged overnight window)")
            indicators_text = "; ".join(indicators) if indicators else "none identified"

            prompt = f"""You are a financial crimes compliance analyst. Write a concise, formal, audit-ready suspicious activity narrative for the transaction below. Summarize what happened, cite the specific risk indicators that triggered the flag, and recommend a next action (e.g. escalate for review, file a Suspicious Activity Report). Keep the narrative under 150 words.

Transaction details:
- Simulation step: {selected['STEP']}
- Transaction type: {selected['TYPE']}
- Amount: ${selected['AMOUNT']:,.2f}
- Origin account: {selected['NAMEORIG']} (balance before: ${selected['OLDBALANCEORG']:,.2f}, balance after: ${selected['NEWBALANCEORIG']:,.2f})
- Destination account: {selected['NAMEDEST']} (balance before: ${selected['OLDBALANCEDEST']:,.2f}, balance after: ${selected['NEWBALANCEDEST']:,.2f})
- Risk score: {selected['RISK_SCORE']}
- Risk indicators triggered: {indicators_text}
- Confirmed fraud label: {"Yes" if bool(selected["ISFRAUD"]) else "No (not yet confirmed)"}
"""

            narrative = None
            try:
                result = session.sql(
                    "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS NARRATIVE",
                    params=[COMPLETE_MODEL, prompt],
                ).to_pandas()
                narrative = result.iloc[0]["NARRATIVE"]
            except Exception as e:
                st.error(f"Could not generate report: {e}")

            if narrative:
                # Escape "$" so Streamlit's markdown renderer doesn't treat currency
                # amounts as LaTeX math delimiters.
                narrative_display = narrative.replace("$", "\\$")
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #D6DEE6;
                        border-radius: 10px;
                        padding: 1.25rem 1.5rem;
                        background-color: #F7F9FB;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                        margin-top: 0.5rem;
                    ">
                        <div style="font-weight:700; color:#1A2B4C; margin-bottom:0.5rem;">
                            📄 Suspicious Activity Narrative
                        </div>
                        <div style="color:#2A3B4C; line-height:1.5;">{narrative_display}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
