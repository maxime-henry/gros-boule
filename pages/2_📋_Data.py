import streamlit as st
from config import fetch_squat_dataframe_cached
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="🍑 Squat data 🍑",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.title("Tu veux de la data ?")
st.subheader("Curieux va")
st.write("---")

# I want this page to display the main stats and graphs
# Uses centralized cached fetch (TTL 120s) for performance
df = fetch_squat_dataframe_cached().copy()
if df.empty:
    st.info("Toujours aucun squat, ça dort debout ?")
    st.stop()

# Préparation de la table
df["date"] = pd.to_datetime(df["date"])
df["date_day"] = df["date"].dt.date
df = df.sort_values(by="date", ascending=False)
df["squats"] = pd.to_numeric(df["squats"])
df["cumulative_squats"] = df.groupby("name")["squats"].cumsum()

metrics_cols = st.columns(4)
metrics_cols[0].metric("Sessions", len(df))
metrics_cols[1].metric("Participants", df["name"].nunique())
metrics_cols[2].metric("Squats totaux", int(df["squats"].sum()))
metrics_cols[3].metric(
    "Dernière session",
    df.iloc[0]["name"],
    delta=int(df.iloc[0]["squats"]),
)

csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Exporter en CSV",
    data=csv_bytes,
    file_name="squats.csv",
    mime="text/csv",
)

sessions_tab, daily_tab, summary_tab = st.tabs(
    [
        "Sessions",
        "Daily pivot",
        "Top squatteurs",
    ]
)

with sessions_tab:
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

with daily_tab:
    pivot = (
        df.groupby(["date_day", "name"])["squats"]
        .sum()
        .reset_index()
        .pivot(index="date_day", columns="name", values="squats")
        .fillna(0)
    )
    st.dataframe(pivot, use_container_width=True)

with summary_tab:
    leaderboard = (
        df.groupby("name")["squats"]
        .agg(["count", "sum"])
        .rename(columns={"count": "Sessions", "sum": "Squats"})
    )
    leaderboard["Moyenne"] = leaderboard["Squats"] / leaderboard["Sessions"]
    leaderboard = leaderboard.sort_values(by="Squats", ascending=False)
    st.dataframe(leaderboard, use_container_width=True)
