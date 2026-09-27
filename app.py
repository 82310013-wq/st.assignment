import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="MSBA325 Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #f8fbff 0%, #edf2f8 100%);
    }
    h1 {
        color: #123d68;
        font-weight: 700;
    }
    h2 {
        color: #1d3557;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

CSV_PATH = "Book2 MSBA325.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)
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
    for col in ["hypertension", "cardiovascular", "diabetes", "no_chronic_condition"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


df = load_data()

st.title("MSBA325 COVID and Chronic Disease Dashboard")
st.caption("Interactive dashboard built from the project dataset")

st.markdown(
    """
    This dashboard explores how COVID-19 case counts relate to chronic disease indicators across towns. It is designed to help a reader understand which towns are most affected and how disease exposure patterns differ across the selected geography.
    """
)

all_towns = ["All towns"] + sorted(df["town"].dropna().unique().tolist())
selected_town = st.sidebar.selectbox("1) Select a town", all_towns)

disease_options = ["All disease types", "Hypertension", "Cardiovascular", "Diabetes"]
selected_disease = st.sidebar.selectbox("2) Select disease type", disease_options)

if selected_town == "All towns":
    filtered = df.copy()
else:
    filtered = df[df["town"] == selected_town]

if selected_disease != "All disease types":
    disease_map = {
        "Hypertension": "hypertension",
        "Cardiovascular": "cardiovascular",
        "Diabetes": "diabetes",
    }
    disease_col = disease_map[selected_disease]
    filtered = filtered[filtered[disease_col] > 0]

if filtered.empty:
    st.warning("No matching data for the selected town and disease type. Please adjust the filters.")
    st.stop()

latest_avg_cases = float(filtered["covid_cases"].mean())
col1, col2 = st.columns(2)
col1.metric("Towns in view", f"{filtered['town'].nunique():,}")
col2.metric("Avg. cases / town", f"{latest_avg_cases:,.1f}")

st.markdown("---")
st.subheader("Main visualizations")

chart_1_data = (
    filtered.groupby("town", as_index=False)["covid_cases"].sum()
    .sort_values("covid_cases", ascending=False)
)
fig1 = px.bar(
    chart_1_data,
    x="covid_cases",
    y="town",
    orientation="h",
    title="COVID-19 cases by town (all towns)",
    labels={"town": "Town", "covid_cases": "COVID cases"},
    template="plotly_white",
    color="covid_cases",
    color_continuous_scale="Blues",
)

infected = filtered[filtered["covid_cases"] > 0].copy()

fig2a = px.bar(
    pd.DataFrame({
        "Status": ["Diabetes", "No diabetes"],
        "COVID_cases": [
            int(infected.loc[infected["diabetes"] == 1, "covid_cases"].sum()),
            int(infected.loc[infected["diabetes"] == 0, "covid_cases"].sum()),
        ],
    }),
    x="COVID_cases",
    y="Status",
    orientation="h",
    title="COVID cases among patients with and without diabetes",
    labels={"Status": "Status", "COVID_cases": "COVID cases"},
    template="plotly_white",
    color="COVID_cases",
    color_continuous_scale="Viridis",
)

fig2b = px.bar(
    pd.DataFrame({
        "Status": ["Hypertension", "No hypertension"],
        "COVID_cases": [
            int(infected.loc[infected["hypertension"] == 1, "covid_cases"].sum()),
            int(infected.loc[infected["hypertension"] == 0, "covid_cases"].sum()),
        ],
    }),
    x="COVID_cases",
    y="Status",
    orientation="h",
    title="COVID cases among patients with and without hypertension",
    labels={"Status": "Status", "COVID_cases": "COVID cases"},
    template="plotly_white",
    color="COVID_cases",
    color_continuous_scale="Plasma",
)

fig2c = px.bar(
    pd.DataFrame({
        "Status": ["Cardiovascular disease", "No cardiovascular disease"],
        "COVID_cases": [
            int(infected.loc[infected["cardiovascular"] == 1, "covid_cases"].sum()),
            int(infected.loc[infected["cardiovascular"] == 0, "covid_cases"].sum()),
        ],
    }),
    x="COVID_cases",
    y="Status",
    orientation="h",
    title="COVID cases among patients with and without cardiovascular disease",
    labels={"Status": "Status", "COVID_cases": "COVID cases"},
    template="plotly_white",
    color="COVID_cases",
    color_continuous_scale="Cividis",
)

fig3 = px.histogram(
    filtered,
    x="covid_cases",
    nbins=20,
    title="Distribution of COVID-19 cases across towns",
    labels={"covid_cases": "COVID cases"},
    template="plotly_white",
    color_discrete_sequence=["#2ca02c"],
)

scatter_data = filtered.copy()
scatter_data["total_chronic_conditions"] = scatter_data[["hypertension", "cardiovascular", "diabetes"]].sum(axis=1)
fig5 = px.scatter(
    scatter_data,
    x="total_chronic_conditions",
    y="covid_cases",
    color="town",
    title="COVID cases vs. chronic condition count",
    labels={"total_chronic_conditions": "Total chronic conditions", "covid_cases": "COVID cases", "town": "Town"},
    template="plotly_white",
)

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(fig1, use_container_width=True)
with row1_col2:
    st.plotly_chart(fig3, use_container_width=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    st.plotly_chart(fig2a, use_container_width=True)
with row2_col2:
    st.plotly_chart(fig2b, use_container_width=True)
with row2_col3:
    st.plotly_chart(fig2c, use_container_width=True)

st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")
st.subheader("Key insights")
st.markdown(
    """
    - Insight 1: The town ranking shows which locations carry the largest COVID burden within the selected view, making the most affected towns immediately visible.
    - Insight 2: The diabetes and hypertension comparisons highlight how chronic conditions are distributed among the infected towns, making disease patterns easier to identify.
    - Insight 3: The case distribution shows whether the selected towns cluster around lower or higher COVID counts without narrowing the view to only the top 10 towns.
    - Insight 4: The scatter plot helps show the relationship between chronic condition burden and COVID case numbers, highlighting whether higher chronic disease counts correspond to greater case intensity.
    """
)

st.caption(f"Current selection: {selected_town} • {selected_disease} • {len(filtered):,} rows")
