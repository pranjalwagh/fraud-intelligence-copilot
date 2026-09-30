-- Chat history for the FRAUD_COPILOT Streamlit app.
-- One row per event. SQL results are never persisted; any "sql" content
-- item is re-run live when a conversation is reloaded.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;
USE WAREHOUSE FRAUD_WH;

CREATE TABLE IF NOT EXISTS CHAT_HISTORY (
    CONVERSATION_ID STRING NOT NULL,
    SEQ NUMBER NOT NULL,
    CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    USER_NAME STRING,
    -- 'user' / 'analyst' (a chat turn) or 'attachment' / 'attachment_clear'
    -- (a document being attached to / removed from the conversation).
    -- PAYLOAD may also carry a top-level "source": "document" tag on
    -- user/analyst rows answered via document Q&A (CORTEX.COMPLETE)
    -- instead of Cortex Analyst.
    ROLE STRING NOT NULL,
    PAYLOAD VARIANT NOT NULL    -- {"content": [...], "source": optional}
    -- Known limitation: SEQ is assigned by a client-side counter (see
    -- next_seq() in the app), not a DB-side sequence, so two browser tabs
    -- open on the same conversation could race and reuse a SEQ value.
);

