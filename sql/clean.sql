-- Cleaning: every raw row gets at most one exclusion rule (the first that applies, in this order),
-- so the data-quality log adds up exactly to the raw row count.
--
--   1 overlap_between_sheets  1-9 Dec 2010 is in both workbook sheets; the copy in the second sheet goes
--   2 exact_duplicate         identical line repeated (all columns equal); first copy kept
--   3 accounting_adjustment   'A' invoices: bad-debt write-offs, not sales
--   4 non_product_line        postage, carriage, fees, manual corrections, discounts, samples,
--                             vouchers, tests: real money, but not product sales
--   5 cancellation            'C' invoices: kept apart for the returns analysis
--   6 stock_write_off         negative quantity outside a cancellation (damaged, missing, "?")
--   7 zero_or_negative_price  free lines and price corrections
--   8 reversed_within_24h     a sale line cancelled in full (same customer, product and quantity) within
--                             24 hours, and that cancellation: an entry error, neither a sale nor a return.
--                             Example: invoice 541431, 74,215 storage jars (GBP 77k), cancelled 16 minutes later.
--
-- Rows with no rule are product sales lines: table sales. Cancellations of product lines: table cancellations.

CREATE OR REPLACE TABLE flagged AS
WITH sheet1_end AS (
    SELECT max(invoice_date) AS t FROM raw_transactions WHERE sheet = 'Year 2009-2010'
),
numbered AS (
    SELECT r.*,
           ROW_NUMBER() OVER (
               PARTITION BY invoice, stock_code, description, quantity, invoice_date, price, customer_id, country
               ORDER BY row_id) AS copy_no
    FROM raw_transactions AS r
    WHERE NOT (r.sheet = 'Year 2010-2011' AND r.invoice_date <= (SELECT t FROM sheet1_end))
)
SELECT r.*,
       CASE
           WHEN n.row_id IS NULL                                   THEN 'overlap_between_sheets'
           WHEN n.copy_no > 1                                      THEN 'exact_duplicate'
           WHEN r.invoice LIKE 'A%'                                THEN 'accounting_adjustment'
           WHEN upper(r.stock_code) IN ('POST', 'DOT', 'C2', 'C3', 'M', 'D', 'S', 'BANK CHARGES', 'ADJUST', 'ADJUST2',
                                        'AMAZONFEE', 'CRUK', 'B', 'PADS', 'TEST001', 'TEST002', 'GIFT')
             OR r.stock_code LIKE 'gift\_%' ESCAPE '\'               THEN 'non_product_line'
           WHEN r.invoice LIKE 'C%'                                THEN 'cancellation'
           WHEN r.quantity < 0                                     THEN 'stock_write_off'
           WHEN r.price <= 0                                       THEN 'zero_or_negative_price'
       END AS rule
FROM raw_transactions AS r
LEFT JOIN numbered AS n USING (row_id);

-- Pair each full cancellation with the latest matching sale line in the 24 hours before it, one to one.
UPDATE flagged SET rule = 'reversed_within_24h'
WHERE row_id IN (
    WITH cand AS (
        SELECT s.row_id AS sale_id, c.row_id AS cancel_id
        FROM flagged AS c
        JOIN flagged AS s
          ON s.rule IS NULL
         AND s.customer_id = c.customer_id
         AND s.stock_code = c.stock_code
         AND s.quantity = -c.quantity
         AND s.invoice_date <= c.invoice_date
         AND s.invoice_date >= c.invoice_date - INTERVAL 24 HOUR
        WHERE c.rule = 'cancellation' AND c.customer_id IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (PARTITION BY c.row_id ORDER BY s.invoice_date DESC, s.row_id DESC) = 1
    ),
    pairs AS (
        SELECT * FROM cand QUALIFY ROW_NUMBER() OVER (PARTITION BY sale_id ORDER BY cancel_id) = 1
    )
    SELECT sale_id FROM pairs UNION ALL SELECT cancel_id FROM pairs
);

CREATE OR REPLACE TABLE dq_log AS
SELECT coalesce(rule, 'kept_as_sale')                    AS rule,
       count(*)                                          AS rows,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct_rows,
       round(sum(quantity * price), 2)                   AS value_gbp
FROM flagged
GROUP BY 1
ORDER BY rows DESC;

CREATE OR REPLACE TABLE sales AS
SELECT row_id, invoice, stock_code, trim(description) AS description, quantity, invoice_date, price,
       quantity * price AS revenue, customer_id, country,
       CAST(date_trunc('month', invoice_date) AS DATE) AS month
FROM flagged
WHERE rule IS NULL;

CREATE OR REPLACE TABLE cancellations AS
SELECT row_id, invoice, stock_code, trim(description) AS description, quantity, invoice_date, price,
       quantity * price AS revenue, customer_id, country,
       CAST(date_trunc('month', invoice_date) AS DATE) AS month
FROM flagged
WHERE rule = 'cancellation';
