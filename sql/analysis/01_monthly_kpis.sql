-- Monthly KPIs. December 2011 stops on the 9th, so it is marked incomplete and left out of trends.
SELECT month,
       round(sum(revenue), 2)                                  AS revenue_gbp,
       count(DISTINCT invoice)                                 AS orders,
       round(sum(revenue) / count(DISTINCT invoice), 2)        AS avg_order_value_gbp,
       count(DISTINCT customer_id)                             AS active_customers,
       sum(quantity)                                           AS units,
       month < DATE '2011-12-01'                               AS complete_month
FROM sales
GROUP BY month
ORDER BY month
