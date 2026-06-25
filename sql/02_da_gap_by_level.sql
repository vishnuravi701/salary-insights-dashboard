# this returns the gap in median salary between Data Analyst and other roles at each experience level
WITH medians AS (
    SELECT 
        experience_level,
        MEDIAN(CASE WHEN job_title = 'Data Analyst' THEN salary_in_usd END) AS analyst_med,
        MEDIAN(CASE WHEN job_title = 'Data Scientist' THEN salary_in_usd END) AS scientist_med,
        MEDIAN(CASE WHEN job_title = 'Data Engineer' THEN salary_in_usd END) AS engineer_med,
        MEDIAN(CASE WHEN job_title = 'Machine Learning Engineer' THEN salary_in_usd END) AS ml_med
    FROM (SELECT DISTINCT * FROM salaries)
    GROUP BY experience_level
)

SELECT 
    experience_level,
    analyst_med,
    analyst_med - scientist_med AS scientist_median_diff,
    analyst_med - engineer_med AS engineer_median_diff,
    analyst_med - ml_med AS ml_median_diff
FROM medians;