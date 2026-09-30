-- OPTIONAL maintenance script: deletes CHAT_HISTORY rows belonging to
-- anonymous viewers (USER_NAME starting with 'anon_') that are older than
-- 30 days. Anonymous viewer identity is only a random id persisted via a
-- URL query param (see get_viewer_name() in the Streamlit app) -- it has no
-- stable owner to expire it, so this script is the manual/scheduled cleanup
-- path instead. Not run automatically; run by hand or wire up as a
-- Snowflake TASK if you want it scheduled.
--
-- Adjust the 30-day cutoff below as needed before running.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;

DELETE FROM FRAUD_HACKATHON.RAW.CHAT_HISTORY
WHERE USER_NAME LIKE 'anon\_%'
  AND CREATED_AT < DATEADD(day, -30, CURRENT_TIMESTAMP());
