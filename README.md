# Online retailer: two-year sales review

A take-home style analysis of a real online retailer's transactions: clean the data, answer the
questions a head of sales would ask, show it on one page, and say what to do next.

**Dashboard:** [`docs/index.html`](docs/index.html) (published with GitHub Pages)
**Data:** [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii), a UK online
gift wholesaler, Dec 2009 – Dec 2011, 1,067,371 transaction lines, licensed CC BY 4.0.

## The questions

1. Is the business growing, and where does the growth come from?
2. Which markets, products and customers carry the revenue?
3. Do new customers come back?
4. How large are cancellations, and is the data trustworthy enough to answer 1–3?
5. What should the team do next quarter?

## Findings

Comparisons use two full 12-month windows (Dec 2009 – Nov 2010 vs Dec 2010 – Nov 2011), because
December 2011 stops on the 9th. Figures are product revenue in GBP after cleaning.

| | Dec 2009 – Nov 2010 | Dec 2010 – Nov 2011 | Change |
|---|---:|---:|---:|
| Revenue | £9.34M | £9.47M | +1.4 % |
| Orders | 19,684 | 18,897 | −4.0 % |
| Average order value | £474 | £501 | +5.7 % |
| Identified customers | 4,236 | 4,292 | +1.3 % |
| Orders per customer | 4.28 | 4.09 | −4.4 % |

- **Growth is small and comes from abroad and from bigger baskets.** UK revenue moved −0.3 %;
  Germany grew 12 %, France 41 %, Spain 32 %. Orders fell 4 % while the average order rose 6 %.
- **Ireland, the second-largest market abroad, fell 26 %.** Worth a look before spending on new markets.
- **Revenue is concentrated.** The top 20 % of products bring 78 % of revenue, the top 20 % of
  customers 74 %. In a recency-frequency-value segmentation, 28 % of customers ("champions") bring
  70 % of revenue.
- **736 formerly frequent customers have gone quiet** (median 142 days since last order); they spent
  £812k last year. They are the cheapest revenue to win back.
- **About one in five new customers buys again in a given later month** (21 % one month after the
  first order, 18 % twelve months after; weighted over 22 and 11 cohorts).
- **38 % of the year's revenue lands in September to November**, 15 % in November alone.
- **Cancellations are 1.9 % of product sales**, once order-entry errors are taken out.

## The data needed work first

Every raw line gets at most one rule, and the counts add up to all 1,067,371 lines
([`sql/clean.sql`](sql/clean.sql), [`reports/tables/00_data_quality_log.csv`](reports/tables/00_data_quality_log.csv)).

| Rule | Lines | Why |
|---|---:|---|
| Kept as product sale | 1,002,009 | |
| Overlap between sheets | 22,523 | 1–9 Dec 2010 is in both sheets of the workbook. Stacking them double-counts it. |
| Cancellation | 16,583 | Kept apart for the returns analysis |
| Exact duplicate | 11,812 | Same line repeated in every column |
| Non-product line | 5,814 | Postage, carriage, Amazon fees, manual corrections, vouchers, test products |
| Stock write-off | 3,391 | Negative quantities outside a cancellation ("damaged", "missing", "?") |
| Reversed within 24 h | 2,662 | A sale cancelled in full by the same customer within a day: an entry error, not a sale and not a return |
| Zero or negative price | 2,571 | Free lines and price corrections |
| Accounting adjustment | 6 | Bad-debt write-offs, the largest −£53,594 |

Two of these change the answer, not just the totals:

- **The sheet overlap.** Without removing it, £409k of December 2010 product revenue is counted twice.
- **Reversed orders.** Invoice 541431 put through 74,215 storage jars (£77k) and was cancelled
  16 minutes later; without the rule, that jar is the fifth best-selling product of the year
  and the cancellation rate is 2.85 % instead of 1.91 %. Some reversals also carried a wrong
  price (invoice 556444: 60 units at £649.50, reversed 11 minutes later at £4.95), which is why the reversed lines net to £37.7k
  rather than zero.

13.4 % of product revenue has no customer id, so customer-level figures (retention, segments)
cover the identified 86.6 % only.

## Recommendations

1. **Win back the at-risk group** with a targeted reorder offer: 736 customers, £812k last year.
2. **Plan stock and staffing for September to November**, when 38 % of revenue is earned.
3. **Grow order count, not only basket size**: orders per customer fell 4.4 %; a reorder reminder for
   frequent buyers targets that directly.
4. **Find out why Ireland fell** before investing in new markets.
5. **Add a quantity and price sanity check at order entry**: 2,662 lines were reversed within a day.

## Method

| Step | File |
|---|---|
| Load the workbook into DuckDB, checking the file's SHA-256 | [`src/retail/load.py`](src/retail/load.py) |
| Clean with one rule per line and a reconciling log | [`sql/clean.sql`](sql/clean.sql) |
| Ten analysis queries: KPIs, year over year, countries, concentration, products, new vs returning, cohorts, RFM, cancellations, seasonality | [`sql/analysis/`](sql/analysis/) |
| Results as CSV | [`reports/tables/`](reports/tables/) |
| Dashboard; every number read from the CSVs | [`src/retail/dashboard.py`](src/retail/dashboard.py) |
| Tests: each cleaning rule on hand-built lines, reconciliation, every query runs | [`tests/`](tests/) |

Choices worth defending:

- **Two full 12-month windows**, not calendar years: the data starts in December and ends on 9 December.
- **The December 2009 cohort is left out of retention**: everyone already active when the data starts
  looks "new" in that month.
- **RFM on quintiles** with a simple, readable segment rule set, because the point is an action list
  for a sales team, not a model. Scores use `CEIL(5 * CUME_DIST())` rather than `NTILE`: most customers
  share a low order count, and `NTILE` splits such ties arbitrarily, so segment counts changed between runs.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
curl -L -o data/raw/online_retail_ii.zip "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
python -m retail.load        # ~50 s; checks the file's SHA-256
python -m retail.analyse     # cleaning + 10 queries, ~1 s
python -m retail.dashboard   # docs/index.html
python -m pytest -q          # 15 tests
```

## Data and licence

Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D, CC BY 4.0.
The raw file is not stored in this repository; the loader checks its checksum. Customer ids in the
source are anonymous numbers.

Designed and reviewed by me, written with an AI coding assistant (Claude Code); every figure
traces to a query and a CSV in this repository.
