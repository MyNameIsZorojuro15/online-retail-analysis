"""Run the cleaning and every analysis query; save each result as CSV in reports/tables/.

Usage: python -m retail.analyse   (after python -m retail.load)
"""
from __future__ import annotations

import time
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "retail.duckdb"
SQL = ROOT / "sql"
TABLES = ROOT / "reports" / "tables"


def clean(con: duckdb.DuckDBPyConnection) -> None:
    con.execute((SQL / "clean.sql").read_text(encoding="utf-8"))


def run_queries(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    out = {}
    for path in sorted((SQL / "analysis").glob("*.sql")):
        out[path.stem] = con.execute(path.read_text(encoding="utf-8")).df()
    return out


def main() -> None:
    t0 = time.perf_counter()
    con = duckdb.connect(str(DB))
    clean(con)
    results = {"00_data_quality_log": con.execute("SELECT * FROM dq_log").df(), **run_queries(con)}
    TABLES.mkdir(parents=True, exist_ok=True)
    for name, df in results.items():
        df.to_csv(TABLES / f"{name}.csv", index=False)
    print({"tables": list(results), "seconds": round(time.perf_counter() - t0, 2)})


if __name__ == "__main__":
    main()
