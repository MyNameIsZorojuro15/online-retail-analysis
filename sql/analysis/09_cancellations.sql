-- Cancelled product value as a share of product sales, per complete month.
WITH s AS (SELECT month, sum(revenue) AS sales FROM sales GROUP BY month),
c AS (SELECT month, -sum(revenue) AS cancelled, count(DISTINCT invoice) AS cancel_invoices FROM cancellations GROUP BY month)
SELECT s.month, round(s.sales, 2) AS sales_gbp, round(coalesce(c.cancelled, 0), 2) AS cancelled_gbp,
       round(100 * coalesce(c.cancelled, 0) / s.sales, 2) AS cancelled_pct, coalesce(c.cancel_invoices, 0) AS cancel_invoices
FROM s LEFT JOIN c USING (month)
WHERE s.month < DATE '2011-12-01'
ORDER BY s.month
