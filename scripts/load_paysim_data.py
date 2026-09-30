"""Uploads the PaySim CSV to a Snowflake stage and loads it into FRAUD_HACKATHON.RAW.PAYSIM.

Run sql/01_setup_database.sql and sql/02_create_paysim_table.sql first.
Requires Python 3.11+ (uses the standard-library `tomllib`) and
snowflake-connector-python (see scripts/requirements.txt) plus a configured
connection. The default connection name is read, in order, from:
  1. the SNOWFLAKE_DEFAULT_CONNECTION_NAME environment variable
  2. ~/.snowflake/connections.toml's [default_connection_name]
  3. ~/.snowflake/config.toml's [default_connection_name] (the Snowflake
     CLI's own config file, checked as a fallback since it's the more
     common place this key lives in a standard `snow` CLI setup)
"""

import os
import tomllib
from pathlib import Path

import snowflake.connector

CSV_PATH = Path(__file__).resolve().parent.parent / "PS_20174392719_1491204439457_log.csv"
CONNECTIONS_FILE = Path.home() / ".snowflake" / "connections.toml"
CONFIG_FILE = Path.home() / ".snowflake" / "config.toml"


def _load_connection_config() -> dict:
    connections_cfg = tomllib.loads(CONNECTIONS_FILE.read_text()) if CONNECTIONS_FILE.exists() else {}

    default_name = os.environ.get("SNOWFLAKE_DEFAULT_CONNECTION_NAME")
    if not default_name:
        default_name = connections_cfg.get("default_connection_name")
    if not default_name and CONFIG_FILE.exists():
        default_name = tomllib.loads(CONFIG_FILE.read_text()).get("default_connection_name")
    if not default_name:
        raise SystemExit(
            "No default connection name found. Set the SNOWFLAKE_DEFAULT_CONNECTION_NAME "
            f"environment variable, or 'default_connection_name' in {CONNECTIONS_FILE} "
            f"or {CONFIG_FILE}."
        )

    # connections.toml can be flat ({name: {...}}) or nested under a
    # top-level "connections" table ({connections: {name: {...}}}) --
    # support both shapes.
    connections = connections_cfg.get("connections", connections_cfg)
    conn_cfg = connections.get(default_name)
    if not conn_cfg:
        raise SystemExit(f"Connection '{default_name}' not found in {CONNECTIONS_FILE}")
    return conn_cfg


def _build_connect_kwargs(conn_cfg: dict) -> dict:
    kwargs = {"account": conn_cfg["account"], "user": conn_cfg["user"]}
    if conn_cfg.get("password"):
        kwargs["password"] = conn_cfg["password"]
        # Respect an explicitly configured authenticator (e.g.
        # "username_password_mfa") even when a password is also present --
        # only default to "snowflake" if the connection didn't specify one.
        kwargs["authenticator"] = conn_cfg.get("authenticator", "snowflake")
    elif conn_cfg.get("private_key_file") or conn_cfg.get("private_key_path"):
        kwargs["private_key_file"] = conn_cfg.get("private_key_file") or conn_cfg.get("private_key_path")
        if conn_cfg.get("private_key_file_pwd"):
            kwargs["private_key_file_pwd"] = conn_cfg["private_key_file_pwd"]
    elif conn_cfg.get("authenticator"):
        kwargs["authenticator"] = conn_cfg["authenticator"]
    else:
        kwargs["authenticator"] = "externalbrowser"
    # Pass through role/warehouse/database/schema/host when the connection
    # config specifies them, instead of only ever using account/user/password
    # (the script still explicitly USEs FRAUD_WH/FRAUD_HACKATHON/RAW below,
    # so this is just about not failing for key-pair/SSO users or roles that
    # need an explicit role/host).
    for key in ("role", "warehouse", "database", "schema", "host"):
        if conn_cfg.get(key):
            kwargs[key] = conn_cfg[key]
    return kwargs


def main() -> None:
    conn_cfg = _load_connection_config()
    conn = snowflake.connector.connect(**_build_connect_kwargs(conn_cfg))
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
        copy_columns = [c[0] for c in cur.description]
        status_idx = copy_columns.index("status") if "status" in copy_columns else 1
        skipped_any = False
        for row in cur:
            print(row)
            if str(row[status_idx]).upper() == "LOAD_SKIPPED":
                skipped_any = True
        if skipped_any:
            print(
                "\nWARNING: at least one file was LOAD_SKIPPED -- Snowflake's load "
                "metadata considers it already loaded (same file name+checksum seen "
                "before). Re-running this script alone will NOT reload it. If you "
                "want a fresh reload, first re-run sql/02_create_paysim_table.sql "
                "(CREATE OR REPLACE TABLE) to reset the table, or add FORCE = TRUE "
                "to the COPY INTO above (which risks duplicate rows if the table "
                "wasn't also reset)."
            )

        cur.execute("SELECT COUNT(*) FROM FRAUD_HACKATHON.RAW.PAYSIM")
        print(f"Total rows loaded: {cur.fetchone()[0]}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
