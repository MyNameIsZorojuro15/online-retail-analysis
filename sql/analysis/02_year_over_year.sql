-- Two comparable 12-month windows: Dec 2009-Nov 2010 (Y1) and Dec 2010-Nov 2011 (Y2).
WITH w AS (
    SELECT *, CASE WHEN month BETWEEN DATE '2009-12-01' AND DATE '2010-11-01' THEN 'Y1'
                   WHEN month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01' THEN 'Y2' END AS yr
    FROM sales
), k AS (
    SELECT yr,
           sum(revenue)                                   AS revenue_gbp,
           count(DISTINCT invoice)                        AS orders,
           sum(revenue) / count(DISTINCT invoice)         AS avg_order_value_gbp,
           count(DISTINCT customer_id)                    AS customers,
           sum(revenue) FILTER (WHERE customer_id IS NOT NULL) / count(DISTINCT customer_id) AS revenue_per_customer_gbp,
           count(DISTINCT invoice) FILTER (WHERE customer_id IS NOT NULL) * 1.0 / count(DISTINCT customer_id) AS orders_per_customer
    FROM w WHERE yr IS NOT NULL GROUP BY yr
)
SELECT m.metric,
       round(max(CASE WHEN yr = 'Y1' THEN v END), 2) AS y1_dec09_nov10,
       round(max(CASE WHEN yr = 'Y2' THEN v END), 2) AS y2_dec10_nov11,
       round(100 * (max(CASE WHEN yr = 'Y2' THEN v END) / max(CASE WHEN yr = 'Y1' THEN v END) - 1), 1) AS change_pct
FROM k
CROSS JOIN LATERAL (VALUES ('revenue_gbp', revenue_gbp), ('orders', orders), ('avg_order_value_gbp', avg_order_value_gbp),
                           ('customers', customers), ('revenue_per_customer_gbp', revenue_per_customer_gbp),
                           ('orders_per_customer', orders_per_customer)) AS m(metric, v)
GROUP BY m.metric
ORDER BY m.metric
