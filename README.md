# The Analyst Pay Gap

An interactive salary-analytics dashboard built with Streamlit, DuckDB, and Plotly on ~93K tech-salary records.

**Live app:** _[link goes here after deploy]_

## The finding

Entry-level pay for Data Analysts, Data Scientists, and Data Engineers sits within about $5K of each other. The gap does not stay small: by senior level, the Data Analyst median trails Data Science by roughly $44K and Data Engineering by roughly $35K. A Mann-Whitney U test confirms the senior DA vs DS gap is real (rank-biserial approximately 0.44, 95% bootstrap CI excludes $0), and it holds with and without duplicate rows removed.

## How it works

- **Data:** `DataScience_salaries_2025.csv`, loaded once and cached.
- **SQL layer:** DuckDB runs SQL directly against the loaded data; every chart's query is viewable in-app under a "SQL behind this" expander.
- **Stats:** a Mann-Whitney U test for the group comparison, and a percentile bootstrap for the confidence interval on the median difference.
- **UI:** four tabs (The Finding, Explore the Data, The Test, Methodology & Limits) with a KPI row and Plotly charts.

## Data limits

- About 97% of rows are mid-size companies, so company-size comparisons are not reliable.
- About 89% of rows are from 2024 to 2025, so there is no meaningful year-over-year trend.
- Remote, hybrid, and on-site rows are pooled; remote arrangement is not a separate axis.
- The executive (EX) level is excluded from the charts (too few rows per role); all headline numbers rest on the EN, MI, and SE levels.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

Note: on Streamlit Community Cloud the app sleeps after a period of inactivity, so the first load after it has been idle can take several seconds to wake and re-run.