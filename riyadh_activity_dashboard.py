import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Riyadh Activity Dashboard", layout="wide")

df = pd.read_csv("cleaned_riyadh_activity.csv")
df["DateG"] = pd.to_datetime(df["DateG"], errors="coerce")

max_score = df["impact_score"].max()
df["activity_level"] = (df["impact_score"] / max_score) * 100

df["event_status"] = df["has_event"].map({0: "No Scheduled Event", 1: "Scheduled Event"})
df["match_status"] = df["has_match"].map({0: "No Match", 1: "Match Day"})
df["weekend_status"] = df["is_weekend"].map({0: "Weekday", 1: "Weekend"})
df["salary_status"] = df["payday_window"].map({0: "Regular Day", 1: "Around Salary Period"})
df["holiday_status"] = df["is_holiday"].map({0: "No Holiday", 1: "Public Holiday"})

# ======================
# Sidebar
# ======================
st.sidebar.title("Dashboard Controls")

date_min = df["DateG"].min()
date_max = df["DateG"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(date_min, date_max)
)

selected_event = st.sidebar.multiselect(
    "Event Status",
    options=df["event_status"].unique(),
    default=list(df["event_status"].unique())
)

selected_salary = st.sidebar.multiselect(
    "Salary Timing",
    options=df["salary_status"].unique(),
    default=list(df["salary_status"].unique())
)

selected_weekend = st.sidebar.multiselect(
    "Day Type",
    options=df["weekend_status"].unique(),
    default=list(df["weekend_status"].unique())
)

show_table = st.sidebar.checkbox("Show Detailed Data", value=False)

filtered_df = df.copy()

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    filtered_df = filtered_df[
        (filtered_df["DateG"] >= start_date) &
        (filtered_df["DateG"] <= end_date)
    ]

filtered_df = filtered_df[
    filtered_df["event_status"].isin(selected_event) &
    filtered_df["salary_status"].isin(selected_salary) &
    filtered_df["weekend_status"].isin(selected_weekend)
]

# ======================
# Title
# ======================
st.title("Riyadh City Activity Dashboard")

st.write("""
This dashboard shows when activity in Riyadh tends to increase and which factors contribute most:
scheduled events, matches, weekends, salary timing, public holidays, and weather.
""")

# ======================
# KPIs
# ======================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Days Analyzed", len(filtered_df))

col2.metric(
    "Average Activity Level",
    f"{filtered_df['activity_level'].mean():.0f}%"
)

col3.metric(
    "Activity on Event Days",
    f"{filtered_df[filtered_df['has_event'] == 1]['activity_level'].mean():.0f}%"
)

col4.metric(
    "Activity on Match Days",
    f"{filtered_df[filtered_df['has_match'] == 1]['activity_level'].mean():.0f}%"
)

st.divider()

# ======================
# Factor Contribution Pie
# ======================
st.subheader("Which Factors Contribute Most to Activity?")

factor_contribution = pd.DataFrame({
    "Factor": [
        "Scheduled Events",
        "Matches",
        "Salary Timing",
        "Weekends",
        "Public Holidays",
        "Weather"
    ],
    "Contribution": [
        (filtered_df["has_event"] * 3).sum(),
        (filtered_df["has_match"] * 2).sum(),
        (filtered_df["payday_window"] * 2).sum(),
        (filtered_df["is_weekend"] * 1).sum(),
        (filtered_df["is_holiday"] * 3).sum(),
        (
            filtered_df["rain_or_mist"] +
            filtered_df["dust"] +
            filtered_df["fog"]
        ).sum()
    ]
})

fig_pie = px.pie(
    factor_contribution,
    names="Factor",
    values="Contribution",
    hole=0.38,
    color_discrete_sequence=[
        "#FF8FAB", "#A7C7E7", "#CDB4DB",
        "#B8E0D2", "#FFCAD4", "#90DBF4"
    ]
)

fig_pie.update_traces(
    textposition="inside",
    textinfo="percent+label"
)

st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ======================
# Helper Function
# ======================
def comparison_chart(data, group_col, title, colors):
    chart_data = (
        data.groupby(group_col)["activity_level"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        chart_data,
        x=group_col,
        y="activity_level",
        color=group_col,
        text="activity_level",
        title=title,
        color_discrete_sequence=colors
    )

    fig.update_traces(
        texttemplate="%{text:.0f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Average Activity Level (%)",
        yaxis=dict(range=[0, 110]),
        showlegend=False,
        height=430,
        margin=dict(l=20, r=20, t=70, b=50)
    )

    return fig

# ======================
# Charts
# ======================
st.subheader("Activity Patterns by Factor")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.plotly_chart(
        comparison_chart(
            filtered_df,
            "event_status",
            "Activity on Scheduled Event Days",
            ["#A7C7E7", "#FF8FAB"]
        ),
        use_container_width=True
    )

with row1_col2:
    st.plotly_chart(
        comparison_chart(
            filtered_df,
            "match_status",
            "Activity on Match Days",
            ["#B8E0D2", "#F7A8B8"]
        ),
        use_container_width=True
    )

with row1_col3:
    st.plotly_chart(
        comparison_chart(
            filtered_df,
            "weekend_status",
            "Weekday vs Weekend Activity",
            ["#CDB4DB", "#90DBF4"]
        ),
        use_container_width=True
    )

row2_col1, row2_col2, row2_col3 = st.columns(3)

with row2_col1:
    salary_effect = pd.DataFrame({
        "Salary Timing": [
            "Regular Days",
            "Few Days Before Salary",
            "Few Days After Salary"
        ],
        "Average Activity Level (%)": [
            filtered_df[
                (filtered_df["days till next payday"] > 3) &
                (filtered_df["days after payday"] > 5)
            ]["activity_level"].mean(),
            filtered_df[filtered_df["days till next payday"] <= 3]["activity_level"].mean(),
            filtered_df[filtered_df["days after payday"] <= 5]["activity_level"].mean()
        ]
    })

    fig_salary = px.bar(
        salary_effect,
        x="Salary Timing",
        y="Average Activity Level (%)",
        color="Salary Timing",
        text="Average Activity Level (%)",
        title="Activity Around Salary Timing",
        color_discrete_sequence=["#BDE0FE", "#FFAFCC", "#CDB4DB"]
    )

    fig_salary.update_traces(
        texttemplate="%{text:.0f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig_salary.update_layout(
        xaxis_title="",
        yaxis_title="Average Activity Level (%)",
        yaxis=dict(range=[0, 110]),
        showlegend=False,
        height=430,
        margin=dict(l=20, r=20, t=70, b=70)
    )

    st.plotly_chart(fig_salary, use_container_width=True)

with row2_col2:
    st.plotly_chart(
        comparison_chart(
            filtered_df,
            "holiday_status",
            "Activity on Public Holidays",
            ["#D8F3DC", "#95D5B2"]
        ),
        use_container_width=True
    )

with row2_col3:
    weather_effect = pd.DataFrame({
        "Weather Type": [
            "Stable Weather",
            "Rain",
            "Dust",
            "Fog"
        ],
        "Average Activity Level (%)": [
            filtered_df[filtered_df["stable_weather"] == 1]["activity_level"].mean(),
            filtered_df[filtered_df["rain_or_mist"] == 1]["activity_level"].mean(),
            filtered_df[filtered_df["dust"] == 1]["activity_level"].mean(),
            filtered_df[filtered_df["fog"] == 1]["activity_level"].mean()
        ]
    })

    fig_weather = px.bar(
        weather_effect,
        x="Weather Type",
        y="Average Activity Level (%)",
        color="Weather Type",
        text="Average Activity Level (%)",
        title="Activity by Weather Condition",
        color_discrete_sequence=["#B8E0D2", "#A7C7E7", "#FFCAD4", "#CDB4DB"]
    )

    fig_weather.update_traces(
        texttemplate="%{text:.0f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig_weather.update_layout(
        xaxis_title="",
        yaxis_title="Average Activity Level (%)",
        yaxis=dict(range=[0, 110]),
        showlegend=False,
        height=430,
        margin=dict(l=20, r=20, t=70, b=50)
    )

    st.plotly_chart(fig_weather, use_container_width=True)

st.divider()

# ======================
# Weather Frequency vs Impact
# ======================
st.subheader("Weather Frequency vs Activity Impact")

weather_analysis = pd.DataFrame({
    "Weather Type": ["Stable Weather", "Rain", "Dust", "Fog"],
    "Frequency (%)": [
        filtered_df["stable_weather"].mean() * 100,
        filtered_df["rain_or_mist"].mean() * 100,
        filtered_df["dust"].mean() * 100,
        filtered_df["fog"].mean() * 100
    ],
    "Activity Impact (%)": [
        filtered_df[filtered_df["stable_weather"] == 1]["activity_level"].mean(),
        filtered_df[filtered_df["rain_or_mist"] == 1]["activity_level"].mean(),
        filtered_df[filtered_df["dust"] == 1]["activity_level"].mean(),
        filtered_df[filtered_df["fog"] == 1]["activity_level"].mean()
    ]
})

fig_weather_scatter = px.scatter(
    weather_analysis,
    x="Frequency (%)",
    y="Activity Impact (%)",
    size="Activity Impact (%)",
    color="Weather Type",
    text="Weather Type",
    title="Weather Conditions: How Often They Occur vs How Strongly They Affect Activity",
    color_discrete_sequence=["#B8E0D2", "#A7C7E7", "#FFCAD4", "#CDB4DB"]
)

fig_weather_scatter.update_traces(
    textposition="top center"
)

fig_weather_scatter.update_layout(
    height=500,
    xaxis_title="Frequency in Dataset (%)",
    yaxis_title="Average Activity Impact (%)",
    margin=dict(l=20, r=20, t=70, b=50)
)

st.plotly_chart(fig_weather_scatter, use_container_width=True)

# ======================
# Optional Detail Table
# ======================
if show_table:
    st.divider()
    st.subheader("Detailed Cleaned Data")

    cols_to_show = [
        "DateG", "Day", "Holiday Name", "Event", "Match",
        "Pay Day", "impact_score", "activity_level"
    ]

    detail_df = filtered_df[cols_to_show].copy()
    detail_df["activity_level"] = detail_df["activity_level"].round(0).astype(int).astype(str) + "%"

    st.dataframe(detail_df, use_container_width=True)