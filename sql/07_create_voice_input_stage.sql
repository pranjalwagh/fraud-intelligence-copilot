-- Voice input stage for the FRAUD_COPILOT Streamlit app.
-- Recorded audio clips are uploaded here (via session.file.put_stream) before
-- being transcribed with AI_TRANSCRIBE. DIRECTORY enables file listing;
-- SNOWFLAKE_SSE is server-side encryption for internal stages.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;
USE WAREHOUSE FRAUD_WH;

CREATE STAGE IF NOT EXISTS VOICE_INPUT_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
