-- Revenue by country in Y2, with share and change vs Y1.
WITH w AS (
    SELECT country, revenue,
           CASE WHEN month BETWEEN DATE '2009-12-01' AND DATE '2010-11-01' THEN 'Y1'
                WHEN month BETWEEN DATE '2010-12-01' AND DATE '2011-11-01' THEN 'Y2' END AS yr
    FROM sales
)
SELECT country,
       round(sum(revenue) FILTER (WHERE yr = 'Y2'), 2)                                         AS y2_revenue_gbp,
       round(100 * sum(revenue) FILTER (WHERE yr = 'Y2') / sum(sum(revenue) FILTER (WHERE yr = 'Y2')) OVER (), 2) AS y2_share_pct,
       round(100 * (sum(revenue) FILTER (WHERE yr = 'Y2') / nullif(sum(revenue) FILTER (WHERE yr = 'Y1'), 0) - 1), 1) AS change_pct
FROM w
WHERE yr IS NOT NULL
GROUP BY country
ORDER BY y2_revenue_gbp DESC NULLS LAST
