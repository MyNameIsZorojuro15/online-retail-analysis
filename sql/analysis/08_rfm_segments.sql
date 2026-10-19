-- RFM segmentation of identified customers active in Y2, measured on 2011-12-01.
-- Scores 1-5 by quintile; segments follow a common rule set (recency first, then frequency).
WITH y2 AS (SELECT * FROM sales WHERE customer_id IS NOT NULL AND month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01'),
base AS (SELECT customer_id,
                datediff('day', max(invoice_date), TIMESTAMP '2011-12-01') AS recency_days,
                count(DISTINCT invoice)                                   AS frequency,
                sum(revenue)                                              AS monetary
         FROM y2 GROUP BY customer_id),
scored AS (SELECT *, 6 - ntile(5) OVER (ORDER BY recency_days) AS r,
                     ntile(5) OVER (ORDER BY frequency)          AS f,
                     ntile(5) OVER (ORDER BY monetary)           AS m
           FROM base),
seg AS (SELECT *, CASE
            WHEN r >= 4 AND f >= 4 THEN '1 Champions'
            WHEN r >= 3 AND f >= 3 THEN '2 Loyal'
            WHEN r >= 4 AND f <= 2 THEN '3 Recent, low frequency'
            WHEN r <= 2 AND f >= 3 THEN '4 At risk (were frequent)'
            WHEN r = 3              THEN '5 Need attention'
            ELSE                         '6 Lapsed' END AS segment
        FROM scored)
SELECT segment, count(*) AS customers,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)            AS customers_pct,
       round(sum(monetary), 2)                                      AS revenue_gbp,
       round(100 * sum(monetary) / sum(sum(monetary)) OVER (), 1)   AS revenue_pct,
       round(median(recency_days))                                  AS median_recency_days,
       round(median(frequency), 1)                                  AS median_orders
FROM seg GROUP BY segment ORDER BY segment
