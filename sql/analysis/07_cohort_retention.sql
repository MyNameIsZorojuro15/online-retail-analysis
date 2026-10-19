-- Monthly acquisition cohorts: share of each cohort that bought again k months after its first month.
-- The December 2009 cohort holds every customer already active when the data starts, so it is excluded.
WITH first AS (SELECT customer_id, min(month) AS cohort FROM sales WHERE customer_id IS NOT NULL GROUP BY customer_id),
act AS (SELECT DISTINCT s.customer_id, f.cohort, datediff('month', f.cohort, s.month) AS k
        FROM sales s JOIN first f USING (customer_id) WHERE s.month < DATE '2011-12-01'),
size AS (SELECT cohort, count(*) AS customers FROM first GROUP BY cohort)
SELECT a.cohort, z.customers, a.k AS months_after,
       round(100.0 * count(*) / z.customers, 1) AS retained_pct
FROM act a JOIN size z USING (cohort)
WHERE a.cohort > DATE '2009-12-01' AND a.cohort < DATE '2011-12-01' AND a.k BETWEEN 0 AND 12
GROUP BY a.cohort, z.customers, a.k
ORDER BY a.cohort, a.k
