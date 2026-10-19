-- Revenue from first-time vs returning identified customers, per month.
-- December 2009 is the first month of data, so every customer there looks "new": it is left out.
WITH first AS (SELECT customer_id, min(month) AS first_month FROM sales WHERE customer_id IS NOT NULL GROUP BY customer_id)
SELECT s.month,
       round(sum(s.revenue) FILTER (WHERE s.month = f.first_month), 2)  AS new_customer_revenue_gbp,
       round(sum(s.revenue) FILTER (WHERE s.month > f.first_month), 2)  AS returning_customer_revenue_gbp,
       count(DISTINCT s.customer_id) FILTER (WHERE s.month = f.first_month) AS new_customers,
       round(100 * sum(s.revenue) FILTER (WHERE s.month > f.first_month) / sum(s.revenue), 1) AS returning_share_pct
FROM sales s JOIN first f USING (customer_id)
WHERE s.month > DATE '2009-12-01' AND s.month < DATE '2011-12-01'
GROUP BY s.month
ORDER BY s.month
