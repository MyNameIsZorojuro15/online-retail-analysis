-- Top 15 products by Y2 revenue, with units and the share of their value that was later cancelled.
WITH s AS (SELECT stock_code, any_value(description) AS description, sum(revenue) AS revenue, sum(quantity) AS units
           FROM sales WHERE month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01' GROUP BY stock_code),
c AS (SELECT stock_code, -sum(revenue) AS cancelled FROM cancellations
      WHERE month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01' GROUP BY stock_code)
SELECT s.stock_code, s.description, round(s.revenue, 2) AS y2_revenue_gbp, s.units,
       round(100 * coalesce(c.cancelled, 0) / s.revenue, 1) AS cancelled_pct_of_sales
FROM s LEFT JOIN c USING (stock_code)
ORDER BY s.revenue DESC
LIMIT 15
