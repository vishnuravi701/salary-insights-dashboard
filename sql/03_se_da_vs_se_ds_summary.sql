SELECT (select median(salary_in_usd) from salaries where job_title = 'Data Analyst') as analyst_median,
       (select median(salary_in_usd) from salaries where job_title = 'Data Scientist') as scientist_median

