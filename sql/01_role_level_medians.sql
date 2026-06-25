# calculate median salary per role and experience level
  SELECT job_title, experience_level,COUNT(*) AS n, MEDIAN(salary_in_usd) AS med
  FROM (SELECT DISTINCT * FROM salaries)
  WHERE job_title = 'Data Analyst' OR job_title = 'Data Scientist' OR job_title = 'Data Engineer' OR job_title = 'Machine Learning Engineer' GROUP BY experience_level, job_title ORDER BY med DESC
