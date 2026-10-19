"""Each cleaning rule on a hand-built set of raw lines, plus the reconciliation the README promises."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from retail.analyse import run_queries

SQL = Path(__file__).resolve().parents[1] / "sql"
T = dt.datetime


def raw_rows():
    r = []
    def add(sheet, invoice, code, qty, when, price, cust=100, country="United Kingdom", desc="MUG"):
        r.append({"row_id": len(r) + 1, "sheet": sheet, "invoice": invoice, "stock_code": code, "description": desc, "quantity": qty,
                  "invoice_date": when, "price": price, "customer_id": cust, "country": country})
    s1, s2 = "Year 2009-2010", "Year 2010-2011"
    add(s1, "500001", "22423", 2, T(2010, 1, 5, 10), 10.0)                     # sale
    add(s1, "500001", "22423", 2, T(2010, 1, 5, 10), 10.0)                     # exact duplicate
    add(s1, "500002", "POST", 1, T(2010, 1, 5, 11), 18.0)                      # non-product
    add(s1, "C500003", "22423", -1, T(2010, 2, 1, 9), 10.0)                     # cancellation (a return)
    add(s1, "500004", "22423", -5, T(2010, 2, 2, 9), 0.0, cust=None, desc="damaged")  # stock write-off
    add(s1, "500005", "85123A", 3, T(2010, 2, 3, 9), 0.0)                       # zero price
    add(s1, "A500006", "B", 1, T(2010, 3, 1, 9), -500.0, cust=None)             # bad-debt adjustment
    add(s1, "500007", "23166", 900, T(2010, 3, 2, 10), 1.0, cust=200)          # entered ...
    add(s1, "C500008", "23166", -900, T(2010, 3, 2, 10, 20), 1.0, cust=200)    # ... and reversed 20 min later
    add(s1, "500009", "22423", 1, T(2010, 12, 3, 9), 10.0, cust=300)           # last sheet-1 day block
    add(s2, "500009", "22423", 1, T(2010, 12, 3, 9), 10.0, cust=300)           # same line again in sheet 2
    add(s2, "500010", "22423", 4, T(2011, 1, 7, 9), 10.0, country="France")   # sale
    return pd.DataFrame(r)


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    df = raw_rows()
    c.register("df", df)
    c.execute("""CREATE TABLE raw_transactions AS SELECT row_id, sheet, invoice, stock_code, description, quantity::INTEGER AS quantity,
                 invoice_date::TIMESTAMP AS invoice_date, price::DOUBLE AS price, CAST(customer_id AS INTEGER) AS customer_id, country FROM df""")
    c.execute((SQL / "clean.sql").read_text(encoding="utf-8"))
    return c


def rule(con, row_id):
    return con.execute("SELECT rule FROM flagged WHERE row_id = ?", [row_id]).fetchone()[0]


@pytest.mark.parametrize("row_id, expected", [
    (1, None), (2, "exact_duplicate"), (3, "non_product_line"), (4, "cancellation"), (5, "stock_write_off"),
    (6, "zero_or_negative_price"), (7, "accounting_adjustment"), (8, "reversed_within_24h"), (9, "reversed_within_24h"),
    (10, None), (11, "overlap_between_sheets"), (12, None),
])
def test_each_rule(con, row_id, expected):
    assert rule(con, row_id) == expected


def test_log_adds_up_to_raw(con):
    assert con.execute("SELECT sum(rows) FROM dq_log").fetchone()[0] == con.execute("SELECT count(*) FROM raw_transactions").fetchone()[0]


def test_sales_and_returns_tables(con):
    assert con.execute("SELECT count(*), sum(revenue) FROM sales").fetchone() == (3, 70.0)
    assert con.execute("SELECT count(*), sum(revenue) FROM cancellations").fetchone() == (1, -10.0)


def test_every_analysis_query_runs(con):
    results = run_queries(con)
    assert len(results) == 10
    shares = results["03_country_mix"]["y2_share_pct"].dropna()
    assert shares.sum() == pytest.approx(100.0, abs=0.05)
