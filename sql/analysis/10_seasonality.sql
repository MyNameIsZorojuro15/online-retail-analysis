-- Share of each 12-month window's revenue earned in September-November.
SELECT CASE WHEN month < DATE '2010-12-01' THEN 'Y1 Dec09-Nov10' ELSE 'Y2 Dec10-Nov11' END AS window,
       round(100 * sum(revenue) FILTER (WHERE month(month) IN (9, 10, 11)) / sum(revenue), 1) AS sep_nov_share_pct,
       round(100 * sum(revenue) FILTER (WHERE month(month) = 11) / sum(revenue), 1)          AS november_share_pct
FROM sales WHERE month < DATE '2011-12-01'
GROUP BY 1 ORDER BY 1
