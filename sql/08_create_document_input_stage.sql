-- Stage for user-uploaded documents (PDF/image) used by the Copilot Chat's
-- "attach document" feature. Extraction is done with AI_PARSE_DOCUMENT.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;
USE WAREHOUSE FRAUD_WH;

CREATE STAGE IF NOT EXISTS DOCUMENT_INPUT_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

