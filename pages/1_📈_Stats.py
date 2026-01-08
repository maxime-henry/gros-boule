import streamlit as st
from config import fetch_squat_dataframe_cached
import pandas as pd
import plotly.express as px

SQUAT_JOUR = 20

st.set_page_config(
    page_title="🍑 Squat stat 🍑",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def fetch_stats_dataframe() -> pd.DataFrame:
    """Use centralized cache for better cross-page performance."""
    df = fetch_squat_dataframe_cached()
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["date_day"] = df["date"].dt.date
    df["squats"] = pd.to_numeric(df["squats"], errors="coerce").fillna(0).astype(int)
    return df.sort_values("date")


st.title("Plus de statistiques")


df = fetch_stats_dataframe()


if df.empty:
    st.info("Pas encore de squats enregistrés pour cette année.")
    st.stop()

names = sorted(df["name"].unique())
selected_names = st.multiselect(
    "Focus équipe",
    options=names,
    default=names,
    placeholder="Choisis un ou plusieurs squatteurs",
)

if not selected_names:
    st.warning("Sélectionne au moins un squatteur pour voir les stats.")
    st.stop()

df = df[df["name"].isin(selected_names)]

if df.empty:
    st.info("Aucune donnée pour cette sélection. Essaye un autre combo.")
    st.stop()

last_update = df["date"].max()
st.caption(
    f"Dataset rafraîchi le {last_update.strftime('%d/%m %H:%M')} • {df['name'].nunique()} squatteurs actifs"
)

total_squats = int(df["squats"].sum())
sessions = int(len(df))
days_tracked = df["date_day"].nunique()
avg_daily_volume = int(df.groupby("date_day")["squats"].sum().mean())

summary_cols = st.columns(4)
summary_cols[0].metric("Squats cumulés", total_squats)
summary_cols[1].metric("Sessions loggées", sessions)
summary_cols[2].metric("Jours actifs", days_tracked)
summary_cols[3].metric("Volume moyen / jour", avg_daily_volume)


daily_squats = (
    df.groupby(["date_day", "name"], as_index=False)["squats"]
    .sum()
    .sort_values("date_day")
)
daily_squats["cumulative_squats"] = daily_squats.groupby("name")["squats"].cumsum()

crew_daily = (
    daily_squats.groupby("date_day", as_index=False)["squats"]
    .sum()
    .rename(columns={"squats": "total_squats"})
)
crew_daily["rolling"] = crew_daily["total_squats"].rolling(7).mean()
goal_line = SQUAT_JOUR * len(selected_names)

first_activity = (
    daily_squats[daily_squats["squats"] > 0]
    .groupby("name")["date_day"]
    .min()
    .rename("first_active_day")
)
filtered_daily = daily_squats.merge(first_activity, on="name", how="left")
filtered_daily = filtered_daily.dropna(subset=["first_active_day"])
filtered_daily = filtered_daily[
    filtered_daily["date_day"] >= filtered_daily["first_active_day"]
].sort_values(["name", "date_day"])

first_logs = (
    df.loc[df.groupby("date_day")["date"].idxmin()].reset_index(drop=True)
    if not df.empty
    else pd.DataFrame()
)
last_logs = (
    df.loc[df.groupby("date_day")["date"].idxmax()].reset_index(drop=True)
    if not df.empty
    else pd.DataFrame()
)

# Calculate average log time per person (in minutes from midnight)
morning_metric = ("—", "")
evening_metric = ("—", "")
if not df.empty:
    df_times = df.copy()
    df_times["time_minutes"] = (
        df_times["date"].dt.hour * 60 + df_times["date"].dt.minute
    )
    avg_time_by_person = df_times.groupby("name")["time_minutes"].mean()

    if not avg_time_by_person.empty:
        # Earliest average = morning person
        morning_name = avg_time_by_person.idxmin()
        morning_avg_minutes = avg_time_by_person.min()
        morning_h, morning_m = divmod(int(morning_avg_minutes), 60)
        morning_metric = (morning_name, f"{morning_h:02d}:{morning_m:02d} moy")

        # Latest average = evening person
        evening_name = avg_time_by_person.idxmax()
        evening_avg_minutes = avg_time_by_person.max()
        evening_h, evening_m = divmod(int(evening_avg_minutes), 60)
        evening_metric = (evening_name, f"{evening_h:02d}:{evening_m:02d} moy")

max_session_row = df.loc[df["squats"].idxmax()]
max_day_row = (
    crew_daily.loc[crew_daily["total_squats"].idxmax()]
    if not crew_daily.empty
    else None
)

totals_by_person = (
    df.groupby("name")["squats"]
    .sum()
    .reset_index()
    .sort_values("squats", ascending=False)
)
avg_by_person = (
    filtered_daily.groupby("name")["squats"].mean().reset_index(name="avg_squats")
    if not filtered_daily.empty
    else pd.DataFrame(columns=["name", "avg_squats"])
)

overview_tab, records_tab, consistency_tab, duos_tab = st.tabs(
    ["📊 Volume", "🏅 Records", "🎯 Régularité", "🫂 Correlations"]
)

with overview_tab:
    if not crew_daily.empty:
        volume_fig = px.bar(
            crew_daily,
            x="date_day",
            y="total_squats",
            title="Volume quotidien de l'équipe",
            color_discrete_sequence=["#ff6f61"],
        )
        volume_fig.add_scatter(
            x=crew_daily["date_day"],
            y=crew_daily["rolling"],
            mode="lines",
            name="Moyenne 7j",
            line=dict(color="#1f1f1f"),
        )
        volume_fig.add_hline(
            y=goal_line,
            line_dash="dot",
            line_color="red",
            opacity=0.8,
        )
        volume_fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Squats",
            margin=dict(l=10, r=10, t=60, b=20),
        )
        st.plotly_chart(volume_fig, width="stretch")

    if not filtered_daily.empty:
        evolution_fig = px.line(
            filtered_daily,
            x="date_day",
            y="squats",
            color="name",
            title="📈 Evolution quotidienne par squatteur",
        )
        evolution_fig.add_hline(
            y=SQUAT_JOUR,
            line_color="red",
            line_dash="dot",
        )
        evolution_fig.update_layout(xaxis_title="Date", yaxis_title="Squats")
        st.plotly_chart(evolution_fig, width="stretch")

        stacked_fig = px.area(
            filtered_daily,
            x="date_day",
            y="cumulative_squats",
            color="name",
            line_group="name",
            title="Squats cumulés par squatteur",
        )
        stacked_fig.update_layout(xaxis_title="Date", yaxis_title="Squats")
        st.plotly_chart(stacked_fig, width="stretch")

with records_tab:
    record_cols = st.columns(4)
    record_cols[0].metric(
        "🏆 Record session",
        max_session_row["name"],
        delta=f"{int(max_session_row['squats'])} squats",
    )
    record_cols[1].metric(
        "📅 Record journée",
        int(max_day_row["total_squats"]) if max_day_row is not None else "—",
        delta=(
            max_day_row["date_day"].strftime("%d/%m")
            if max_day_row is not None
            else None
        ),
    )
    record_cols[2].metric(
        "⏰ Squatteur du matin",
        morning_metric[0],
        delta=morning_metric[1],
        delta_color="off",
    )
    record_cols[3].metric(
        "🌙 Squatteur du soir",
        evening_metric[0],
        delta=evening_metric[1],
        delta_color="off",
    )

    if not crew_daily.empty:
        top_days = crew_daily.sort_values("total_squats", ascending=False).head(10)
        top_day_fig = px.bar(
            top_days,
            x="total_squats",
            y=top_days["date_day"].astype(str),
            orientation="h",
            title="Top 10 journées les plus squattées",
        )
        top_day_fig.add_vline(x=goal_line, line_color="red", line_dash="dot")
        top_day_fig.update_layout(xaxis_title="Squats", yaxis_title="Date")
        st.plotly_chart(top_day_fig, width="stretch")

    if not totals_by_person.empty:
        totals_fig = px.bar(
            totals_by_person,
            x="squats",
            y="name",
            title="Somme des squats par squatteur",
            orientation="h",
        )
        totals_fig.update_layout(xaxis_title="Squats", yaxis_title=None)
        st.plotly_chart(totals_fig, width="stretch")

    if not avg_by_person.empty:
        avg_sorted = avg_by_person.sort_values("avg_squats", ascending=False)
        avg_fig = px.bar(
            avg_sorted,
            x="name",
            y="avg_squats",
            title="Moyenne journalière par squatteur",
        )
        avg_fig.add_hline(y=SQUAT_JOUR, line_color="red", line_dash="dot")
        avg_fig.update_layout(xaxis_title=None, yaxis_title="Squats")
        st.plotly_chart(avg_fig, width="stretch")

with consistency_tab:
    hist_fig = px.histogram(
        df,
        x="squats",
        nbins=40,
        title="Distribution des squats par session",
        color_discrete_sequence=["#ff6f61"],
    )
    hist_fig.add_vline(x=SQUAT_JOUR, line_color="red", line_dash="dot")
    hist_fig.update_layout(xaxis_title="Squats", yaxis_title="Sessions")
    st.plotly_chart(hist_fig, width="stretch")

    if not filtered_daily.empty:
        filtered_no_zero = filtered_daily[filtered_daily["squats"] > 0]
        if not filtered_no_zero.empty:
            std_by_person = filtered_no_zero.groupby("name")["squats"].std()
            std_by_person = std_by_person.dropna()
            if not std_by_person.empty:
                consistent = std_by_person.idxmin()
                chaotic = std_by_person.idxmax()
                std_cols = st.columns(2)
                std_cols[0].metric(
                    "🎯 Squatteur le plus régulier",
                    consistent,
                    delta=f"σ={std_by_person.min():.1f}",
                )
                std_cols[1].metric(
                    "🎲 Squatteur le plus freestyle",
                    chaotic,
                    delta=f"σ={std_by_person.max():.1f}",
                )

            box_fig = px.box(
                filtered_no_zero,
                x="name",
                y="squats",
                title="📊 Distribution journalière",
            )
            box_fig.add_hline(y=SQUAT_JOUR, line_color="red", line_dash="dot")
            box_fig.update_layout(xaxis_title="Squatteur", yaxis_title="Squats")
            st.plotly_chart(box_fig, width="stretch")

with duos_tab:
    if filtered_daily.empty:
        st.info("Pas assez de données pour corréler les squatteurs.")
    else:
        sessions_count = filtered_daily.groupby("name")["date_day"].nunique()
        eligible_names = sessions_count[sessions_count >= 5].index.tolist()
        if len(eligible_names) < 2:
            st.info(
                "Encore trop peu de jours loggés pour comparer les rythmes (minimum 5 jours chacun)."
            )
        else:
            corr_base = filtered_daily[filtered_daily["name"].isin(eligible_names)]
            pivot_df = (
                corr_base.pivot_table(
                    index="date_day",
                    columns="name",
                    values="squats",
                    aggfunc="sum",
                )
                .fillna(0)
                .sort_index()
            )
            correlation_matrix = pivot_df.corr()
            corr_fig = px.imshow(
                correlation_matrix,
                labels=dict(x="Squatteur", y="Squatteur", color="Corr"),
                color_continuous_scale="Viridis",
            )
            corr_fig.update_layout(
                title="🫂 Correlation entre squatteurs",
                xaxis_title=None,
                yaxis_title=None,
            )
            st.plotly_chart(corr_fig, width="stretch")
            st.caption("Minimum 5 jours loggés chacun pour apparaître dans le heatmap.")

            pairs = []
            columns = correlation_matrix.columns.tolist()
            for i in range(len(columns)):
                for j in range(i + 1, len(columns)):
                    pairs.append(
                        {
                            "s1": columns[i],
                            "s2": columns[j],
                            "value": correlation_matrix.iloc[i, j],
                        }
                    )

            if pairs:
                pair_df = pd.DataFrame(pairs)
                best_pair = pair_df.loc[pair_df["value"].idxmax()]
                worst_pair = pair_df.loc[pair_df["value"].idxmin()]

                def render_pair_chart(pair_row, title: str):
                    names_pair = [pair_row["s1"], pair_row["s2"]]
                    pair_data = filtered_daily[filtered_daily["name"].isin(names_pair)]
                    if pair_data.empty:
                        return
                    min_start = pair_data.groupby("name")["date_day"].min().max()
                    pair_data = pair_data[pair_data["date_day"] >= min_start]
                    pair_fig = px.line(
                        pair_data,
                        x="date_day",
                        y="squats",
                        color="name",
                        title=title,
                    )
                    pair_fig.add_hline(y=SQUAT_JOUR, line_color="red", line_dash="dot")
                    pair_fig.update_layout(xaxis_title="Date", yaxis_title="Squats")
                    st.plotly_chart(pair_fig, width="stretch")

                render_pair_chart(
                    best_pair,
                    f"📈 {best_pair['s1']} x {best_pair['s2']} : duo synchronisé ({best_pair['value']:.2f})",
                )
                render_pair_chart(
                    worst_pair,
                    f"📉 {worst_pair['s1']} vs {worst_pair['s2']} : opposés ({worst_pair['value']:.2f})",
                )
