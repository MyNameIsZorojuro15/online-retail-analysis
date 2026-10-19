"""Load the UCI Online Retail II workbook into DuckDB, untouched, as table raw_transactions.

Source: UCI Machine Learning Repository, dataset 502 (Chen, 2012), CC BY 4.0.
https://archive.ics.uci.edu/dataset/502/online+retail+ii
Two sheets (2009-2010 and 2010-2011) are stacked; the sheet name is kept for traceability.

Usage: python -m retail.load   (expects data/raw/online_retail_ii.zip; checks its SHA-256 first)
"""
from __future__ import annotations

import hashlib
import time
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "data" / "raw" / "online_retail_ii.zip"
DB = ROOT / "data" / "retail.duckdb"
SHA256 = "572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb"
URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not ZIP.exists():
        raise SystemExit(f"Download {URL} to {ZIP} first.")
    if sha256(ZIP) != SHA256:
        raise SystemExit("Checksum mismatch: not the file this analysis was built on.")
    t0 = time.perf_counter()
    with zipfile.ZipFile(ZIP) as z, z.open("online_retail_II.xlsx") as fh:
        sheets = pd.read_excel(fh, sheet_name=None, dtype={"Invoice": str, "StockCode": str, "Description": str, "Country": str})
    frames = []
    for name, df in sheets.items():
        df = df.rename(columns={"Customer ID": "customer_id", "Invoice": "invoice", "StockCode": "stock_code", "Description": "description",
                                "Quantity": "quantity", "InvoiceDate": "invoice_date", "Price": "price", "Country": "country"})
        df["sheet"] = name
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw["row_id"] = range(1, len(raw) + 1)
    con = duckdb.connect(str(DB))
    con.execute("DROP TABLE IF EXISTS raw_transactions")
    con.register("raw_df", raw)
    con.execute("""CREATE TABLE raw_transactions AS
                   SELECT row_id, sheet, invoice, stock_code, description, quantity::INTEGER AS quantity,
                          invoice_date::TIMESTAMP AS invoice_date, price::DOUBLE AS price,
                          CAST(customer_id AS INTEGER) AS customer_id, country
                   FROM raw_df""")
    n = con.execute("SELECT count(*) FROM raw_transactions").fetchone()[0]
    print({"rows": n, "sheets": list(sheets), "seconds": round(time.perf_counter() - t0, 1)})


if __name__ == "__main__":
    main()
