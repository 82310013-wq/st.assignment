import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import altair as alt
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "assignment_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def save_chart_as_html(chart, filename):
    html_content = chart.to_html()
    target_path = OUTPUT_DIR / f"{filename}.html"
    target_path.write_text(html_content, encoding="utf-8")
    return target_path


def build_dashboard_html(charts):
    dashboard_html = """<html>
    <head>
        <meta charset=\"utf-8\" />
        <title>MSBA325 COVID Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 24px; background: #f9fafb; }
            h1, h2 { color: #1f2937; }
            .chart-block { margin-bottom: 28px; padding: 18px; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        </style>
    </head>
    <body>
        <h1>MSBA325 COVID and Chronic Disease Dashboard</h1>
    """

    for name, chart in charts.items():
        chart_html = chart.to_html()
        dashboard_html += f"<div class=\"chart-block\"><h2>{name.replace('_', ' ').title()}</h2>{chart_html}</div>"

    dashboard_html += "</body></html>"
    return dashboard_html


def save_dashboard_snapshot(charts):
    dashboard_html = build_dashboard_html(charts)
    (OUTPUT_DIR / "dashboard_summary.html").write_text(dashboard_html, encoding="utf-8")


def export_all_visuals(charts):
    for chart_name, chart in charts.items():
        save_chart_as_html(chart, chart_name)
    save_dashboard_snapshot(charts)
    return OUTPUT_DIR


st.set_page_config(page_title="MSBA325 COVID Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%);
    }
    h1 {
        color: #123a5a;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    h2, h3 {
        color: #1d3557;
    }
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #edf5ff 100%);
        border: 1px solid #dfeaf6;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        box-shadow: 0 4px 12px rgba(13, 49, 90, 0.06);
    }
    .small-note {
        color: #55657a;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("MSBA325 COVID and Chronic Disease Dashboard")
st.caption("A policy-focused view of COVID-19 burden and chronic disease patterns across towns.")

@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "Book2 MSBA325.csv",
        base_dir / "MSBA325" / "Book2 MSBA325.csv",
        Path("Book2 MSBA325.csv"),
        Path("MSBA325") / "Book2 MSBA325.csv",
    ]

    csv_path = next((candidate for candidate in candidates if candidate.exists()), None)
    if csv_path is None:
        raise FileNotFoundError("Could not find the dataset 'Book2 MSBA325.csv'. Check that the file exists in the project folder or in a sibling 'MSBA325' folder.")

    df = pd.read_csv(csv_path)

    df = df.rename(
        columns={
            "Existence of chronic diseases_hypertension": "hypertension",
            "Existence of chronic diseaseas_does not exist": "no_chronic_condition",
            "Town": "town",
            "Nb of Covid-19 cases": "covid_cases",
            "Existence of chronic diseases_cardiovascular diseases": "cardiovascular",
            "Existence of chronic diseases_Diabetes": "diabetes",
        }
    )

    df["town"] = df["town"].astype(str).str.strip()
    df["covid_cases"] = pd.to_numeric(df["covid_cases"], errors="coerce").fillna(0).astype(int)

    for col in ["hypertension", "no_chronic_condition", "cardiovascular", "diabetes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["total_chronic_conditions"] = df[["hypertension", "cardiovascular", "diabetes"]].sum(axis=1)
    return df


df = load_data()

st.sidebar.header("Filters")
max_towns = st.sidebar.slider("Number of towns to display", 5, 20, 10)

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
summary_col1.markdown(
    f"<div class='metric-card'><div class='small-note'>Total towns</div><h3>{df.shape[0]:,}</h3></div>",
    unsafe_allow_html=True,
)
summary_col2.markdown(
    f"<div class='metric-card'><div class='small-note'>Total COVID cases</div><h3>{df['covid_cases'].sum():,}</h3></div>",
    unsafe_allow_html=True,
)
summary_col3.markdown(
    f"<div class='metric-card'><div class='small-note'>Avg. cases / town</div><h3>{df['covid_cases'].mean():,.0f}</h3></div>",
    unsafe_allow_html=True,
)
summary_col4.markdown(
    f"<div class='metric-card'><div class='small-note'>Towns with chronic disease</div><h3>{int(df[['hypertension', 'cardiovascular', 'diabetes']].max(axis=1).sum()):,}</h3></div>",
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader("Executive snapshot")

# 1. Top towns by COVID cases
chart_1_data = df.nlargest(max_towns, "covid_cases")[['town', 'covid_cases']].sort_values('covid_cases', ascending=True)
chart_1 = alt.Chart(chart_1_data).mark_bar(color="#4C78A8").encode(
    x=alt.X('covid_cases:Q', title='COVID-19 cases'),
    y=alt.Y('town:N', sort='-x', title='Town'),
    tooltip=['town:N', 'covid_cases:Q']
).properties(title='Top towns by COVID-19 cases', height=420)

# 2. Chronic disease prevalence by type
chart_2_data = pd.DataFrame({
    'Disease': ['Hypertension', 'Cardiovascular', 'Diabetes'],
    'Count': [df['hypertension'].sum(), df['cardiovascular'].sum(), df['diabetes'].sum()]
}).sort_values('Count', ascending=False)
chart_2 = alt.Chart(chart_2_data).mark_bar(color="#F58518").encode(
    x=alt.X('Count:Q', title='Number of towns'),
    y=alt.Y('Disease:N', sort='-x', title='Condition'),
    tooltip=['Disease:N', 'Count:Q']
).properties(title='Chronic disease prevalence by type', height=320)

# 3. Breakdown of disease presence share
with_chronic_condition = int(df[["hypertension", "cardiovascular", "diabetes"]].max(axis=1).sum())
without_chronic_condition = int(df['no_chronic_condition'].sum())

presence_counts = pd.DataFrame({
    'Category': ['At least one chronic condition', 'No chronic condition'],
    'Count': [with_chronic_condition, without_chronic_condition]
})
chart_3 = alt.Chart(presence_counts).mark_arc().encode(
    theta='Count:Q',
    color=alt.Color('Category:N', scale=alt.Scale(range=['#54A24B', '#E45756'])),
    tooltip=['Category:N', 'Count:Q']
).properties(title='Share of towns with chronic disease status')

# 4. Distribution of COVID-19 case counts
chart_4 = alt.Chart(df).mark_bar(opacity=0.8, color="#72B7B2").encode(
    alt.X('covid_cases:Q', bin=alt.Bin(maxbins=20), title='COVID-19 cases'),
    y='count()',
    tooltip=['count()']
).properties(title='Distribution of COVID-19 cases across towns', height=320)

# 5. Scatter plot: chronic conditions vs COVID cases
chart_5 = alt.Chart(df).mark_circle(size=80, color="#B279A2").encode(
    x=alt.X('total_chronic_conditions:Q', title='Total chronic conditions in town'),
    y=alt.Y('covid_cases:Q', title='COVID-19 cases'),
    color=alt.Color('hypertension:Q', scale=alt.Scale(scheme='viridis')),
    tooltip=['town:N', 'covid_cases:Q', 'total_chronic_conditions:Q']
).properties(title='Relationship between chronic conditions and COVID-19 cases', height=320)

tabs = st.tabs(["Overview", "Town comparison", "Chronic disease", "Case distribution"])

with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_1, width="stretch")
    with col2:
        st.altair_chart(chart_2, width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        st.altair_chart(chart_3, width="stretch")
    with col4:
        st.altair_chart(chart_4, width="stretch")

    st.altair_chart(chart_5, width="stretch")

with tabs[1]:
    st.altair_chart(chart_1, width="stretch")

with tabs[2]:
    st.altair_chart(chart_2, width="stretch")
    st.altair_chart(chart_3, width="stretch")

with tabs[3]:
    st.altair_chart(chart_4, width="stretch")
    st.altair_chart(chart_5, width="stretch")

dashboard_charts = {
    "chart_1_top_towns_by_covid_cases": chart_1,
    "chart_2_chronic_disease_prevalence_by_type": chart_2,
    "chart_3_share_of_towns_with_chronic_disease_status": chart_3,
    "chart_4_distribution_of_covid_19_cases": chart_4,
    "chart_5_relationship_between_chronic_conditions_and_covid_cases": chart_5,
}

st.markdown("---")
st.subheader("Embedded dashboard preview")
components.html(build_dashboard_html(dashboard_charts), height=1400, scrolling=True)

if st.button("Save all visuals to this device", type="primary"):
    export_all_visuals(dashboard_charts)
    st.success(f"Saved all 5 visuals and the dashboard to: {OUTPUT_DIR}")

# keep the auto-save too, but the button is the fastest/manual path
export_all_visuals(dashboard_charts)
st.caption("Dataset: COVID-19 cases and chronic disease indicators by town.")
