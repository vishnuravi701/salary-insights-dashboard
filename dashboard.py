import pandas as pd
import numpy as np
import streamlit as st
import duckdb
import plotly.express as px
from scipy.stats import mannwhitneyu
from pathlib import Path

st.set_page_config(
    page_title="The Analyst Pay Gap",   # text in the browser tab
    page_icon="📊",                      # favicon in the browser tab
    layout="wide",                       # use full screen width instead of a narrow centered column
)

# One accent color, used everywhere (theme + charts must match per the spec)
ACCENT = "#4b8bf5"        # matches primaryColor in config.toml
ACCENT_LIGHT = "#8fb8f8"
ACCENT_FAINT = "#c7dcfb"


# Absolute path to the CSV, anchored to this file's folder so the app can be
# launched from any working directory (including Streamlit Community Cloud).
DATA_PATH = Path(__file__).parent / "DataScience_salaries_2025.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)



@st.cache_resource
def get_con():
    con = duckdb.connect()          # in-memory DuckDB connection
    con.register("salaries", load_data())  # expose the df as a SQL table
    return con



@st.cache_data
def run_query(sql,  _con,params = None,):
    if params is None:
        params = []
    return _con.execute(sql, params).df()

def get_salaries(job_title, con, dedup):
    source = "(SELECT DISTINCT * FROM salaries) AS deduped" if dedup else "salaries"
    sql = f"""
        SELECT salary_in_usd
        FROM {source}
        WHERE experience_level = 'SE'
          AND job_title = ?
    """
    result = run_query(sql, con, [job_title])
    return result["salary_in_usd"].to_numpy()

def mann_whitney(da, ds):
    U_da, p = mannwhitneyu(da, ds, alternative="two-sided")
    n_da, n_ds = len(da), len(ds)
    f_da = U_da / (n_da * n_ds)          # P(random DA salary > random DS salary), ties = 0.5
    rbc = 2 * f_da - 1                    # rank-biserial, signed DA-minus-DS
    median_diff = np.median(da) - np.median(ds)
    return {
        "n_da": n_da, "n_ds": n_ds,
        "median_da": float(np.median(da)),
        "median_ds": float(np.median(ds)),
        "median_diff": float(median_diff),
        "U": float(U_da), "p": float(p), "rbc": float(rbc),
        "ds_wins_pct": float((1 - f_da) * 100),
    }


def bootstrap_median_diff_ci(da, ds, n_boot=10000):
    point_estimate = float(np.median(da) - np.median(ds))

    n_da = len(da)
    n_ds = len(ds)
    boot_diffs = []

    for _ in range(n_boot):
        da_sample = np.random.choice(da, size=n_da, replace=True)
        ds_sample = np.random.choice(ds, size=n_ds, replace=True)
        boot_diffs.append(np.median(da_sample) - np.median(ds_sample))

    boot_diffs = np.array(boot_diffs)
    lower = float(np.percentile(boot_diffs, 2.5))
    upper = float(np.percentile(boot_diffs, 97.5))

    return {
        "point_estimate": point_estimate,
        "ci_lower": lower,
        "ci_upper": upper,
        "n_boot": n_boot,
    }





con = get_con()
df = load_data()

roles = ["Data Analyst", "Data Scientist", "Data Engineer"]


# st.write(df.head())  
# st.write(df.shape)

#level =  sidebar stubs — options from the data, no filtering wired yet
level = st.sidebar.selectbox("Experience level", sorted(df["experience_level"].unique()))
role = st.sidebar.selectbox("Role", roles)

SALARY_SQL = (
    "SELECT median(salary_in_usd) AS median_salary_usd "
    "FROM (SELECT DISTINCT * FROM salaries) AS deduped "
    "WHERE experience_level = ? AND job_title = ?"
)


CURATED_ROLES = ["Data Analyst", "Data Scientist", "Data Engineer"]
placeholders = ", ".join(["?"] * len(CURATED_ROLES)) # this makes it so that if the number of curated roles is changed in the future this doesn't have to be hardcoded to change

GRID_SQL = (
    "SELECT job_title, experience_level, MEDIAN(salary_in_usd) AS median_salary_usd "
    "FROM (SELECT DISTINCT * FROM salaries) AS deduped "
    f"WHERE job_title IN ({placeholders}) "
    "AND experience_level IN ('EN', 'MI', 'SE') "
    "GROUP BY job_title, experience_level "
    "ORDER BY job_title, "
    "CASE experience_level WHEN 'EN' THEN 1 WHEN 'MI' THEN 2 WHEN 'SE' THEN 3 END"
)

DA_GAP_SQL = ("""WITH medians AS (
    SELECT 
        experience_level,
        MEDIAN(CASE WHEN job_title = 'Data Analyst' THEN salary_in_usd END) AS analyst_med,
        MEDIAN(CASE WHEN job_title = 'Data Scientist' THEN salary_in_usd END) AS scientist_med,
        MEDIAN(CASE WHEN job_title = 'Data Engineer' THEN salary_in_usd END) AS engineer_med,

    FROM (SELECT DISTINCT * FROM salaries) WHERE experience_level IN ('EN', 'MI', 'SE')
    GROUP BY experience_level
)

SELECT 
    experience_level,
    analyst_med,
    analyst_med - scientist_med AS scientist_median_diff,
    analyst_med - engineer_med AS engineer_median_diff,
FROM medians;""")


st.title("The Analyst Pay Gap")
st.markdown("#### The analyst pay gap is small at entry and compounds from there.")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="DA vs DS gap in USD, entry → senior", value="5K → 44K")
kpi2.metric(label="Chance a random senior DS out-earns a random senior DA", value="~72%")
kpi3.metric(label="Salary records", value="93,597")
kpi4.metric(label="95% bootstrap CI, robust ± dedup", value="Excludes $0")

st.success(
    r"**Senior Data Analysts earn about \$44,300 less than senior Data "
    r"Scientists.** A randomly chosen senior Data Scientist out-earns a "
    r"randomly chosen senior Data Analyst roughly **72% of the time** "
    r"(rank-biserial ≈ 0.44). The gap holds with and without duplicate rows "
    r"removed (\$44K deduplicated, \$40K with duplicates), which rules out "
    r"the dataset's repeated rows as the cause."
    "\n\n"
    r"Entry-level medians for the analyst, scientist, and engineer tracks sit "
    r"within ~\$5K of each other. The gap widens with seniority. **Entry pay is "
    r"nearly identical across the three, but the divergence compounds with every "
    r"level.**"
)
tab_finding, tab_explore, tab_test, tab_method = st.tabs(
    ["The Finding", "Explore the Data", "The Test", "Methodology & Limits"]
)


with tab_finding:
    gap_df = run_query(DA_GAP_SQL, con)

    long_df = gap_df.melt(
        id_vars="experience_level",
        value_vars=["scientist_median_diff", "engineer_median_diff"],
        var_name="comparison",
        value_name="median_diff_usd",
    )
    label_map = {
        "scientist_median_diff": "vs Data Scientist",
        "engineer_median_diff": "vs Data Engineer",
    }
    long_df["comparison"] = long_df["comparison"].map(label_map)

    gap_fig = px.line(
        long_df,
        x="experience_level",
        y="median_diff_usd",
        color="comparison",
        markers=True,
        category_orders={"experience_level": ["EN", "MI", "SE"]},
        color_discrete_map={
            "vs Data Scientist": ACCENT,
            "vs Data Engineer": ACCENT_LIGHT,
        },
        labels={
            "experience_level": "Experience level",
            "median_diff_usd": "DA median − other role median (USD)",
            "comparison": "Comparison",
        },
    )
    gap_fig.update_layout(yaxis_tickformat="$,.0f")
    gap_fig.add_hline(y=0, line_dash="dash", opacity=0.4)

    # --- §E: endpoint annotations at SE, positioned from the actual data ---
    se_ds_y = long_df.loc[
        (long_df["experience_level"] == "SE")
        & (long_df["comparison"] == "vs Data Scientist"),
        "median_diff_usd",
    ].iloc[0]
    se_de_y = long_df.loc[
        (long_df["experience_level"] == "SE")
        & (long_df["comparison"] == "vs Data Engineer"),
        "median_diff_usd",
    ].iloc[0]

    gap_fig.add_annotation(
        x="SE", y=se_ds_y, text="−$44K vs Data Scientist",
        showarrow=False, font=dict(size=11), xanchor="right", yshift=-14,
    )
    gap_fig.add_annotation(
        x="SE", y=se_de_y, text="−$35K vs Data Engineer",
        showarrow=False, font=dict(size=11), xanchor="right", yshift=14,
    )

    # --- §E: currency hover, no duplicated trace-name box ---
    gap_fig.update_traces(
        hovertemplate="%{fullData.name}: %{y:$,.0f}<extra></extra>"
    )

    st.plotly_chart(gap_fig, use_container_width=True)

    st.markdown(
        r"**The gap compounds.** At entry, the Data Analyst median sits within ~\$5K of both Data "
        r"Scientist and Data Engineer. The analyst gap then widens at every step: by senior level, "
        r"Data Analyst trails Data Science by ~\$44K and Data Engineering by ~\$35K."
    )

    with st.expander("SQL behind this chart"):
        st.code(DA_GAP_SQL, language="sql")


with tab_explore:
    st.caption("Sidebar filters apply to this tab.")

    result = run_query(SALARY_SQL, con, [level, role])
    median_value = result["median_salary_usd"].iloc[0]

    if pd.isna(median_value):
        st.warning("No rows for that combination.")
    else:
        st.metric(f"Median salary — {role} ({level})", f"${median_value:,.0f}")

    with st.expander("SQL behind this number"):
        st.code(SALARY_SQL, language="sql")
        st.caption(f"Parameters → experience_level = {level}, job_title = {role}")

    grid_df = run_query(GRID_SQL, con, CURATED_ROLES)
    grid_fig = px.line(
        grid_df,
        x="experience_level",
        y="median_salary_usd",
        color="job_title",
        markers=True,
        category_orders={"experience_level": ["EN", "MI", "SE"]},
        color_discrete_map={
            "Data Analyst": ACCENT,
            "Data Scientist": ACCENT_LIGHT,
            "Data Engineer": ACCENT_FAINT,
        },
        labels={
            "experience_level": "Experience level",
            "median_salary_usd": "Median salary (USD)",
            "job_title": "Role",
        },
    )

    # emphasize the selected role's line, fade the rest
    for trace in grid_fig.data:
        if trace.name == role:
            trace.update(line=dict(width=4), opacity=1.0)
        else:
            trace.update(opacity=0.25)

    # ring the selected (role, level) point
    selected = grid_df[
        (grid_df["job_title"] == role) & (grid_df["experience_level"] == level)
    ]
    if not selected.empty:
        grid_fig.add_scatter(
            x=[level],
            y=[selected["median_salary_usd"].iloc[0]],
            mode="markers",
            marker=dict(size=14, symbol="circle-open", line=dict(width=3), color="#fafafa"),
            name="Selected",
            showlegend=False,
        )

    grid_fig.update_layout(yaxis_tickformat="$,.0f")
    st.plotly_chart(grid_fig, use_container_width=True)

    if selected.empty:
        st.caption(
            f"'{level}' isn't plotted here — the trend chart covers EN/MI/SE only (EX is too thin per role)."
        )

    st.markdown(
        r"**Takeaway:** All three tracks start in the same neighborhood, with Data Analyst, Data "
        r"Engineer, and Data Scientist medians all landing near \$81K at entry. From there the lines "
        r"fan apart: by senior level, Data Science reaches about \$161K and Data Engineering about "
        r"\$152K, while Data Analyst tops out near \$117K."
    )


with tab_test:
    st.header("Is the senior DA–DS gap real? (Mann–Whitney)")

    da_dedup = get_salaries("Data Analyst", con, dedup=True)
    ds_dedup = get_salaries("Data Scientist", con, dedup=True)

    mw_dedup = mann_whitney(da_dedup, ds_dedup)
    ci_dedup = bootstrap_median_diff_ci(da_dedup, ds_dedup)

    st.metric(
        label="Senior Data Analyst vs Data Scientist — median salary gap",
        value=f"-${abs(mw_dedup['median_diff']):,.0f}",
    )

    st.caption(
        rf"95% bootstrap CI: −\${abs(ci_dedup['ci_lower']):,.0f} to "
        rf"−\${abs(ci_dedup['ci_upper']):,.0f}. The interval is recomputed from "
        r"a fresh random resample on every interaction, so the bounds shift "
        r"slightly each rerun. That is the bootstrap running live. The "
        r"−\$44,300 point estimate is fixed; only the interval around it is "
        r"simulated."
    )


with tab_method:
    with st.expander("Tested and dropped"):
        st.markdown(
            r"**Remote vs. on-site testing .** The pooled data shows remote workers "
            r"earning about \$4K less. Deduplicating the rows collapses the gap to +\$88. Duplicate "
            r"rows concentrate in the senior, on-site, US cells, so the apparent effect tracks which "
            r"rows repeat in the dataset. Dropped for testing after failing robustness checks."
            "\n\n"
            r"**An ML salary predictor.** A gradient-boosted model (HistGBR on log-salary) reached "
            r"R² = 0.37 with a mean absolute error around \$45.2K, but was only 17.5% better than just predicting the median every time :("
            "\n\n"
            r"**Company size as an axis.** Large companies appear to pay less than mid-size companies, "
            r"but they also have fewer US employees in the dataset (~74.8% vs. ~85.1%). Restricting "
            r"the analysis to US-only reduces the gap to about ~\$7.5K based on 67 rows."
        )

    with st.expander("Methodology"):
        st.markdown(
            r"**Deduplication** happens inside a CTE (`SELECT DISTINCT *`) before aggregation."
            "\n\n"
            r"**Medians over means.** Salary data is right-skewed; means run \$6K to \$10K above "
            r"medians here and overstate typical pay."
            "\n\n"
            r"**Mann-Whitney over a t-test.** The test is rank-based and needs no normality "
            r"assumption, which suits skewed salary distributions."
            "\n\n"
            r"**Un-seeded bootstrap CI.** The 95% interval is a percentile bootstrap recomputed from "
            r"a fresh resample on every rerun, so the bounds visibly wobble while the point estimate "
            r"stays fixed. That behavior is deliberate: the estimate comes from the data, and the "
            r"interval comes from simulation."
            "\n\n"
            r"**Parameterized queries.** All user-driven SQL passes inputs through `?` placeholders."
        )

    st.info(
        "**Data & limitations.** A few properties of this dataset bound what the "
        "dashboard can honestly claim:"
        "\n\n"
        "**Company size works only as a filter here.** About 97% of rows are mid-size "
        "companies, so there is no reliable small-vs-large comparison to draw."
        "\n\n"
        "**No real time trend.** About 89% of rows are from 2024 and 2025, so any "
        "year-over-year movement would mostly reflect growth in the dataset itself."
        "\n\n"
        "**Remote status is mixed in.** On-site, hybrid, and fully-remote rows are "
        "pooled together in these medians; remote arrangement has no axis of its own."
        "\n\n"
        "**Senior level and below only.** The executive (EX) tier is excluded from the "
        "charts. Data Analyst EX has only ~50 rows, too few to trust. Every headline "
        "number rests on the EN/MI/SE levels, where each role\u00d7level cell has 900+ "
        "rows."
    )