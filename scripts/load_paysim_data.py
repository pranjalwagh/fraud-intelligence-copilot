"""Uploads the PaySim CSV to a Snowflake stage and loads it into FRAUD_HACKATHON.RAW.PAYSIM.

Run sql/01_setup_database.sql and sql/02_create_paysim_table.sql first.
Requires snowflake-connector-python (pip install snowflake-connector-python) and a
configured connection in ~/.snowflake/connections.toml.
"""

import tomllib
from pathlib import Path

import snowflake.connector

CSV_PATH = Path(__file__).resolve().parent.parent / "PS_20174392719_1491204439457_log.csv"
CONNECTIONS_FILE = Path.home() / ".snowflake" / "connections.toml"


def main() -> None:
    cfg = tomllib.loads(CONNECTIONS_FILE.read_text())
    conn_name = cfg["default_connection_name"]
    conn_cfg = cfg[conn_name]

    conn = snowflake.connector.connect(
        account=conn_cfg["account"],
        user=conn_cfg["user"],
        password=conn_cfg.get("password"),
        authenticator="externalbrowser" if "password" not in conn_cfg else "snowflake",
    )
    cur = conn.cursor()
    try:
        cur.execute("USE WAREHOUSE FRAUD_WH")
        cur.execute("USE DATABASE FRAUD_HACKATHON")
        cur.execute("USE SCHEMA RAW")

        print("Uploading CSV to stage...")
        cur.execute(
            f"PUT 'file://{CSV_PATH.as_posix()}' @FRAUD_HACKATHON.RAW.PAYSIM_STAGE "
            "AUTO_COMPRESS=TRUE OVERWRITE=TRUE PARALLEL=8"
        )
        for row in cur:
            print(row)

        print("Loading data into PAYSIM...")
        cur.execute(
            """
            COPY INTO FRAUD_HACKATHON.RAW.PAYSIM
            FROM @FRAUD_HACKATHON.RAW.PAYSIM_STAGE
            FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
            ON_ERROR = 'ABORT_STATEMENT'
            """
        )
        for row in cur:
            print(row)

        cur.execute("SELECT COUNT(*) FROM FRAUD_HACKATHON.RAW.PAYSIM")
        print(f"Total rows loaded: {cur.fetchone()[0]}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
