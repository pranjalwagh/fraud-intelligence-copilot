-- FRAUD_COPILOT Streamlit app deployment
-- The app uses a warehouse runtime created with FROM '@stage' (not the legacy
-- ROOT_LOCATION parameter), so files only copy into the app at CREATE time.
-- After ANY change to streamlit_app/*, re-run steps 2 and 3 below or the change
-- will not appear in the running app.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;
USE WAREHOUSE FRAUD_WH;

-- 1. Stage that holds the app source files. No FILE_FORMAT needed -- this
--    stage holds Python/YAML source files, not CSV data (unlike PAYSIM_STAGE).
CREATE STAGE IF NOT EXISTS FRAUD_COPILOT_STAGE
  DIRECTORY = (ENABLE = TRUE);

-- Upload files to the stage first (run from the repo root so the relative
-- paths below resolve):
--   PUT 'file://streamlit_app/fraud_copilot_streamlit_app.py' @FRAUD_COPILOT_STAGE OVERWRITE=TRUE AUTO_COMPRESS=FALSE;
--   PUT 'file://streamlit_app/environment.yml' @FRAUD_COPILOT_STAGE OVERWRITE=TRUE AUTO_COMPRESS=FALSE;
--   ALTER STAGE FRAUD_COPILOT_STAGE REFRESH;

-- 2. (Re)create the Streamlit object from the current stage contents.
CREATE OR REPLACE STREAMLIT FRAUD_COPILOT
  FROM '@FRAUD_HACKATHON.RAW.FRAUD_COPILOT_STAGE'
  MAIN_FILE = 'fraud_copilot_streamlit_app.py'
  QUERY_WAREHOUSE = 'FRAUD_WH';

-- 3. Promote the new version to live so viewers see the change immediately.
ALTER STREAMLIT FRAUD_COPILOT ADD LIVE VERSION FROM LAST;
