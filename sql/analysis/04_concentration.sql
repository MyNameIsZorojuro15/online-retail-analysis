-- How concentrated is Y2 revenue? Share taken by the top 20 % of products and of identified customers.
WITH y2 AS (SELECT * FROM sales WHERE month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01'),
p AS (SELECT stock_code, sum(revenue) AS r, ntile(5) OVER (ORDER BY sum(revenue) DESC) AS q FROM y2 GROUP BY stock_code),
c AS (SELECT customer_id, sum(revenue) AS r, ntile(5) OVER (ORDER BY sum(revenue) DESC) AS q FROM y2 WHERE customer_id IS NOT NULL GROUP BY customer_id)
SELECT 'products' AS entity, count(*) AS n, round(100 * sum(r) FILTER (WHERE q = 1) / sum(r), 1) AS top20_share_pct FROM p
UNION ALL
SELECT 'customers', count(*), round(100 * sum(r) FILTER (WHERE q = 1) / sum(r), 1) FROM c
