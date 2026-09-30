-- FRAUD_FLAGS view
-- Flags TRANSFER/CASH_OUT transactions that drained the origin account,
-- flags overnight-window transactions, and rolls both into a simple RISK_SCORE.
--
-- Design note: the balance-drain flag (2 pts) is the strong, standalone
-- signal -- on its own it already reaches ~97.6% recall / 100% precision on
-- this dataset (see README). The overnight flag (1 pt) is a secondary,
-- supplementary signal that only adds context/severity to a transaction
-- that's already flagged by the drain rule; by design it never reaches the
-- RISK_SCORE >= 2 threshold on its own. This is intentional, not a bug.

USE DATABASE FRAUD_HACKATHON;
USE SCHEMA RAW;
USE WAREHOUSE FRAUD_WH;

CREATE OR REPLACE VIEW FRAUD_FLAGS AS
WITH BASE AS (
    SELECT
        STEP,
        TYPE,
        AMOUNT,
        NAMEORIG,
        OLDBALANCEORG,
        NEWBALANCEORIG,
        NAMEDEST,
        OLDBALANCEDEST,
        NEWBALANCEDEST,
        ISFRAUD,
        ISFLAGGEDFRAUD,
        (TYPE IN ('TRANSFER', 'CASH_OUT')
            AND ABS(AMOUNT - OLDBALANCEORG) <= 0.01
            AND OLDBALANCEORG > 0) AS IS_BALANCE_DRAIN,
        -- Simulation steps are 1-based hours; MOD(STEP, 24) BETWEEN 0 AND 8
        -- covers the last hour of one simulated day (mod = 0, e.g. step 24,
        -- 48, ...) through hour 8 of the next -- a 9-hour "overnight" window.
        (MOD(STEP, 24) BETWEEN 0 AND 8) AS IS_OVERNIGHT
    FROM FRAUD_HACKATHON.RAW.PAYSIM
)
SELECT
    STEP,
    TYPE,
    AMOUNT,
    NAMEORIG,
    OLDBALANCEORG,
    NEWBALANCEORIG,
    NAMEDEST,
    OLDBALANCEDEST,
    NEWBALANCEDEST,
    ISFRAUD,
    ISFLAGGEDFRAUD,
    IS_BALANCE_DRAIN,
    IS_OVERNIGHT,
    (CASE WHEN IS_BALANCE_DRAIN THEN 2 ELSE 0 END
     + CASE WHEN IS_OVERNIGHT THEN 1 ELSE 0 END) AS RISK_SCORE
FROM BASE;

