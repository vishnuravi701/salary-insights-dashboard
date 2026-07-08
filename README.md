# The Analyst Pay Gap

Data Analyst pay starts within about $5K of Data Science and Data Engineering, then falls roughly $44K behind by the senior level. This dashboard surfaces that gap and tests whether it holds up.

**Live demo:** https://salary-insights-dashboard-9obq.streamlit.app/

Built with Streamlit, DuckDB, and Plotly on ~93K tech-salary records.

## The finding

Entry-level salaries for Data Analysts, Data Scientists, and Data Engineers are fairly similar, with median pay differing by only about $5K. As careers progress, however, the gap widens considerably. By the senior level, the median salary for Data Analysts is roughly $44K lower than Data Scientists and about $35K lower than Data Engineers. A Mann-Whitney U test indicates that the difference between senior Data Analysts and Data Scientists is statistically significant (rank-biserial correlation ≈ 0.44), and the 95% bootstrap confidence interval excludes zero. The result remains consistent even after removing duplicate rows from the dataset.

## How it works

- **Data:** `DataScience_salaries_2025.csv`, loaded once and cached.
- **SQL layer:** DuckDB runs SQL directly against the loaded data; every chart's query is viewable in-app under a "SQL behind this" expander.
- **Stats:** a Mann-Whitney U test for the group comparison, and a percentile bootstrap for the confidence interval on the median difference.
- **UI:** four tabs (The Finding, Explore the Data, The Test, Methodology & Limits) with a KPI row and Plotly charts.

## Data limits

- ~97% of rows are mid-size companies, so there is no reliable small-vs-large comparison.
- ~89% of rows are from 2024 to 2025, so there is no meaningful year-over-year trend.
- Remote, hybrid, and on-site rows are pooled; remote arrangement is not a separate axis.
- The executive (EX) level is excluded from the charts (too few rows per role); all headline numbers rest on EN, MI, and SE.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

Note: on Streamlit Community Cloud the app sleeps after a period of inactivity, so the first load after it has been idle can take several seconds to wake and re-run.