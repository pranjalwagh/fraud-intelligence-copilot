-- OPTIONAL: grants needed for a role OTHER than the object owner. Not run by
-- default -- this project is currently deployed and owned by a single
-- ACCOUNTADMIN-equivalent role. Replace <ROLE_NAME> and run the statements
-- you actually need if you're granting access to another role.
--
-- Streamlit-in-Snowflake (warehouse runtime, which is what this app uses)
-- always executes with the OWNER's rights, privileges, warehouse, database
-- and schema -- never the caller/viewer's. That means a role only needs
-- USAGE on the app object itself to open and use it; it does NOT need
-- direct SELECT/INSERT/READ/WRITE on the underlying tables, views, semantic
-- view or stages, because the app's own queries always run as the owner
-- regardless of who's viewing it.
--
-- Section A is therefore the only grant needed to let <ROLE_NAME> open and
-- use FRAUD_COPILOT. Section B is only needed if <ROLE_NAME> should ALSO be
-- able to query these objects directly (e.g. from a worksheet or another
-- app), outside of FRAUD_COPILOT.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;

-- =====================================================================
-- Section A: required to view/use the FRAUD_COPILOT Streamlit app.
-- =====================================================================
GRANT USAGE ON DATABASE FRAUD_HACKATHON TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA FRAUD_HACKATHON.RAW TO ROLE <ROLE_NAME>;
GRANT USAGE ON STREAMLIT FRAUD_HACKATHON.RAW.FRAUD_COPILOT TO ROLE <ROLE_NAME>;

-- =====================================================================
-- Section B: OPTIONAL -- only needed if <ROLE_NAME> queries these objects
-- directly, outside of the app (e.g. in a worksheet, notebook, or another
-- Cortex Analyst client against the semantic view).
-- =====================================================================
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <ROLE_NAME>;
GRANT USAGE ON WAREHOUSE FRAUD_WH TO ROLE <ROLE_NAME>;
GRANT SELECT ON TABLE FRAUD_HACKATHON.RAW.PAYSIM TO ROLE <ROLE_NAME>;
GRANT SELECT ON VIEW FRAUD_HACKATHON.RAW.FRAUD_FLAGS TO ROLE <ROLE_NAME>;
-- SELECT (not USAGE) is the privilege required to query a semantic view.
GRANT SELECT ON SEMANTIC VIEW FRAUD_HACKATHON.RAW.FRAUD_SEMANTIC TO ROLE <ROLE_NAME>;
GRANT READ ON STAGE FRAUD_HACKATHON.RAW.VOICE_INPUT_STAGE TO ROLE <ROLE_NAME>;
GRANT READ ON STAGE FRAUD_HACKATHON.RAW.DOCUMENT_INPUT_STAGE TO ROLE <ROLE_NAME>;
GRANT SELECT, INSERT ON TABLE FRAUD_HACKATHON.RAW.CHAT_HISTORY TO ROLE <ROLE_NAME>;
