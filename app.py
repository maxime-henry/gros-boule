from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_cookies_controller import CookieController

from motivation import motivate
from config import (
    load_all,
    mistral_chat,
    Participant,
    save_new_squat,
    today,
    end_of_year,
)


st.set_page_config(
    page_title="🍑 Squat app 🍑", page_icon="🍑", initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    :root {
        --peach:#ff6f61;
        --dark:#1f1f1f;
        --cream:#fff3ea;
        --card:#ffffff11;
    }
    .main {
        background: radial-gradient(circle at top, #ffe0b2 0%, #ffd1dc 25%, #ffeede 60%, #ffffff 100%);
    }
    .hero-card {
        background: rgba(255,255,255,0.65);
        border-radius: 24px;
        padding: 1.5rem 2rem;
        box-shadow: 0 25px 60px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,111,97,0.15);
    }
    .pulse-card {
        background: rgba(255, 255, 255, 0.55);
        border-radius: 20px;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(255,111,97,0.1);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        width: 100%;
    }
    .trend-card {
        border-radius: 18px;
        padding: 1rem 1.5rem;
        background: rgba(255,255,255,0.8);
        border: 1px solid rgba(255,111,97,0.12);
    }
    .login-grid button {
        border-radius: 999px !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        background: white !important;
        color: #111 !important;
        font-weight: 600 !important;
    }
    .login-grid button:hover {
        background: var(--peach) !important;
        color: white !important;
    }
    .stat-chip {
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,111,97,0.12);
        color: #b43821;
        font-size: 0.85rem;
        display: inline-flex;
        gap: 0.4rem;
        align-items: center;
    }
    @media (max-width: 768px) {
        .block-container {
            padding: 0.6rem 0.8rem 2.5rem !important;
        }
        .hero-card,
        .pulse-card,
        .trend-card {
            padding: 1rem;
        }
        .stat-grid {
            grid-template-columns: 1fr;
        }
        .login-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.75rem;
        }
        .login-grid button,
        .stButton button {
            width: 100%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# LOAD and DEFINE the DATA here ######################################

participants = (
    "Audrix",
    "Matix",
    "Floflox",
    "Max",
    "Marinox",
    "Viox",
    "Carlix",
    "Annax",
    "Elix",
    "Le K",
    "Tonix",
    "Fannux",
    "Andreax",
    # "Thouvenix",
)


SQUAT_JOUR = 20

DAYS_LEFT = (end_of_year - today).days + 1


def chunked_sequence(items, size):
    """Yield successive chunks sized for responsive metric grids."""
    size = max(1, size)
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def render_metric_rows(metric_items, per_row):
    for group in chunked_sequence(metric_items, per_row):
        cols = st.columns(len(group))
        for col, metric in zip(cols, group):
            col.metric(
                metric["label"],
                metric["value"],
                delta=metric.get("delta"),
                help=metric.get("help"),
            )


# Mobile-first by default; append ?view=desktop to the URL for the wide layout.
try:
    query_params = st.query_params  # Streamlit >= 1.40 exposes a proxy attribute
except AttributeError:  # Back-compat for earlier versions
    query_params = st.experimental_get_query_params()

if not isinstance(query_params, dict):
    query_params = dict(query_params)

mobile_view = query_params.get("view", ["mobile"])[0].lower() != "desktop"


@st.cache_data(ttl=120)
def fetch_squat_dataframe():
    """Centralise la récupération des squats (1 scan Dynamo = 1 cache hit)."""
    df = load_all()
    return df.sort_values("date")


def refresh_squat_dataframe():
    """Permet de purger le cache après un enregistrement."""
    fetch_squat_dataframe.clear()  # type: ignore[attr-defined]


squat_data = fetch_squat_dataframe()
data_total = squat_data.copy()
crew_daily_totals = pd.DataFrame(columns=["date_day", "squats"])
if not squat_data.empty:
    crew_daily_totals = (
        squat_data.assign(date_day=squat_data["date"].dt.date)
        .groupby("date_day")["squats"]
        .sum()
        .reset_index()
    )
    crew_daily_totals["rolling"] = crew_daily_totals["squats"].rolling(7).mean()

start_of_year = datetime(today.year, 1, 1).date()
days_elapsed = (today.date() - start_of_year).days + 1
crew_total_squats = int(data_total["squats"].sum()) if not data_total.empty else 0
crew_goal_to_date = len(participants) * SQUAT_JOUR * days_elapsed
crew_delta_today = crew_total_squats - crew_goal_to_date
crew_goal_full_year = (
    len(participants) * SQUAT_JOUR * ((end_of_year.date() - start_of_year).days + 1)
)
crew_completion_pct = (
    (crew_total_squats / crew_goal_full_year) * 100 if crew_goal_full_year else 0
)
last_entry = data_total.iloc[-1] if not data_total.empty else None


# --- Initialisation de st.session_state ---
today_date = today.date()  # Get today's date in UTC


participants_obj = {}
for name in participants:
    participants_obj[name] = Participant(
        name, squat_data, days_left=DAYS_LEFT, squat_objectif_quotidien=SQUAT_JOUR
    )

active_today = sum(
    1
    for participant in participants_obj.values()
    if participant.sum_squats_done_today >= SQUAT_JOUR
)
best_streak_holder = max(
    participants_obj.values(),
    key=lambda p: p.best_objective_streak,
    default=None,
)
pace_leader = max(
    participants_obj.values(),
    key=lambda p: p.moyenne_squats_par_jour,
    default=None,
)


# COOKIES CONTROL ##################################################################################################################
controller = CookieController()
cookies = controller.getAll()
id_squatteur_from_cookies = cookies.get("id_squatteur", None)
#####################################################################################################################################

participant_order = list(participants)
participant_obj = (
    participants_obj.get(id_squatteur_from_cookies)
    if id_squatteur_from_cookies
    else None
)


def clear_login_cookie():
    """Reset the participant cookie so someone else can se connecter."""
    try:
        controller.delete("id_squatteur")  # type: ignore[attr-defined]
    except AttributeError:
        controller.set("id_squatteur", "", expires=datetime.now() - timedelta(days=1))


if (
    id_squatteur_from_cookies is not None
    and id_squatteur_from_cookies in participant_order
):

    participant_order.remove(id_squatteur_from_cookies)
    participant_order.insert(0, id_squatteur_from_cookies)

    st.title(f"Allez {id_squatteur_from_cookies}, t'es pas une merde!! ")

    if st.button(
        "Pas toi ? Clique ici pour changer de squatteur", key="change_user_btn"
    ):
        clear_login_cookie()
        st.rerun()

    participant_obj = participants_obj.get(id_squatteur_from_cookies)

    placeholder = st.empty()
    placeholder.info("Fait un squat en attendant au pire non ?")

    st.divider()

    st.write(
        f"{id_squatteur_from_cookies}, maintenant tu peux directement enregistrer tes squats ici :"
    )

    with st.form("squat_form"):
        squats_faits = st.number_input(
            "Enregistrer une session squats :",
            min_value=5,
            max_value=600,
            value=20,
            step=1,
        )
        submitted = st.form_submit_button(
            f"Enregistrer pour {id_squatteur_from_cookies} 🍑"
        )

    if submitted:
        with st.spinner("Saving..."):
            # Sauvegarder dans DynamoDB
            new_item = save_new_squat(id_squatteur_from_cookies, squats_faits)

            refresh_squat_dataframe()
            participant_obj = participants_obj[id_squatteur_from_cookies] = Participant(
                id_squatteur_from_cookies,
                fetch_squat_dataframe(),
                days_left=DAYS_LEFT,
                squat_objectif_quotidien=SQUAT_JOUR,
            )

            size = len(motivate)
            random_motivate = random.randrange(0, size)
            st.success(motivate[random_motivate])

            # secure_cookie = (
            #     st.runtime.exists() and st.runtime.scriptrunner.streamlit_cloud
            # )

            id_squatteur = id_squatteur_from_cookies
            controller.set(
                "id_squatteur",
                id_squatteur,
                expires=datetime.now() + timedelta(days=5, hours=1),
                # secure=True,
                # same_site="Strict" if secure_cookie else "Lax",
            )
            st.rerun()

    if participant_obj is not None:
        st.subheader("Ton cockpit 🍑")
        cockpit_metrics = [
            {"label": "Total cumulé", "value": int(participant_obj.sum_squats_done)},
            {
                "label": "Delta vs objectif",
                "value": int(participant_obj.delta_done_vs_objecitf_today),
                "help": "Positif = avance, négatif = retard",
            },
            {
                "label": "Squats aujourd'hui",
                "value": int(participant_obj.sum_squats_done_today),
                "delta": int(participant_obj.sum_squats_done_today - SQUAT_JOUR),
            },
            {
                "label": "Moyenne / jour",
                "value": round(float(participant_obj.moyenne_squats_par_jour), 2),
                "delta": round(
                    float(participant_obj.moyenne_squats_par_jour - SQUAT_JOUR), 2
                ),
            },
        ]
        render_metric_rows(cockpit_metrics, per_row=1 if mobile_view else 2)

        streak_metrics = [
            {
                "label": "🔥 Streak en cours",
                "value": f"{participant_obj.current_objective_streak} jours",
                "delta": f"Record {participant_obj.best_objective_streak}",
            },
            {
                "label": "📚 Sessions loggées",
                "value": participant_obj.sessions_logged,
                "delta": f"Depuis {participant_obj.premier_squat_date.strftime('%d/%m')}",
            },
            {
                "label": "📈 Progression annuelle",
                "value": f"{participant_obj.progress_pct_vs_objectif:.1f}%",
                "delta": f"Objectif {participant_obj.objectif_sum_squat}",
            },
        ]
        render_metric_rows(streak_metrics, per_row=1 if mobile_view else 2)

        trend_metrics = [
            {
                "label": "Semaine en cours",
                "value": participant_obj.weekly_total,
                "delta": participant_obj.weekly_delta,
            },
            {
                "label": "Projection fin d'année",
                "value": participant_obj.projected_year_total,
                "delta": int(
                    participant_obj.projected_year_total
                    - participant_obj.objectif_sum_squat
                ),
                "help": "Projection basée sur ta moyenne quotidienne",
            },
            {
                "label": "Hier",
                "value": int(participant_obj.sum_squats_hier),
                "delta": int(participant_obj.sum_squats_hier - SQUAT_JOUR),
            },
        ]
        render_metric_rows(trend_metrics, per_row=1 if mobile_view else 2)

        st.progress(
            min(participant_obj.progress_pct_vs_objectif / 100, 1.0),
            text="Progression sur l'objectif annuel",
        )
        st.caption("Barre verte = ton pourcentage du défi annuel. Continue d'empiler.")

        if mobile_view:
            chart_col = st.container()
            box_col = st.container()
        else:
            chart_col, box_col = st.columns([3, 2])
        personal_history = participant_obj.df.copy()
        personal_history["date"] = pd.to_datetime(personal_history["date"])
        with chart_col:
            fig = px.bar(
                personal_history, x="date", y="squats", title="Sessions récentes"
            )
            fig.update_layout(
                shapes=[
                    {
                        "type": "line",
                        "yref": "y",
                        "y0": SQUAT_JOUR,
                        "y1": SQUAT_JOUR,
                        "xref": "paper",
                        "x0": 0,
                        "x1": 1,
                        "line": {"color": "red", "width": 2},
                    }
                ],
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        with box_col:
            box_fig = px.box(personal_history, y="squats", title="Distribution")
            st.plotly_chart(box_fig, use_container_width=True)


else:
    st.title("🍑 Squat App 🍑")
    st.subheader("New year new me")
    st.caption("La persévérance, secret de tous les triomphes. - Victor Hugo")

    st.subheader("Choisis ton nom pour te connecter")
    st.caption("Clique sur ton nom, on te prépare le formulaire perso juste après 👇")
    login_container = st.container()
    login_container.markdown('<div class="login-grid">', unsafe_allow_html=True)
    selection_cols = login_container.columns(1 if mobile_view else 3)
    for idx, name in enumerate(participants):
        col = selection_cols[idx % len(selection_cols)]
        if col.button(f"{name} 🔓", key=f"login_{name}", use_container_width=True):
            controller.set(
                "id_squatteur",
                name,
                expires=datetime.now() + timedelta(days=5, hours=1),
            )
            st.rerun()
    login_container.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="hero-card">', unsafe_allow_html=True)
if mobile_view:
    hero_cols = [st.container(), st.container()]
else:
    hero_cols = st.columns([3, 2])
with hero_cols[0]:
    st.write(
        "🔥 20 squats par jour jusqu'au 31 décembre. On compte les reps, pas les excuses."
    )
with hero_cols[1]:
    st.metric(
        label="Challenge complété",
        value=f"{crew_completion_pct:.1f}%",
        delta=f"{crew_total_squats} squats loggés",
    )
    st.progress(
        min(crew_completion_pct / 100, 1.0),
        text="Progression de l'équipe sur l'année",
    )

crew_metrics = [
    {
        "label": "Equipe en piste",
        "value": len(participants),
        "delta": f"{active_today} validés aujourd'hui",
    },
    {"label": "Jours restants", "value": DAYS_LEFT},
    {
        "label": "Delta collectif",
        "value": int(crew_delta_today),
        "help": "Positif = avance cumulative par rapport à l'objectif",
    },
    {"label": "Squats cumulés", "value": crew_total_squats},
]
render_metric_rows(crew_metrics, per_row=1 if mobile_view else 2)
st.markdown("</div>", unsafe_allow_html=True)


st.subheader("Crew pulse")
pulse_metrics = [
    {
        "label": "♾️ Longest streak",
        "value": best_streak_holder.name if best_streak_holder else "—",
        "delta": (
            f"{best_streak_holder.best_objective_streak} jours"
            if best_streak_holder
            else None
        ),
    },
    {
        "label": "⚡ Pace leader",
        "value": pace_leader.name if pace_leader else "—",
        "delta": (
            f"{round(float(pace_leader.moyenne_squats_par_jour), 2)} / jour"
            if pace_leader
            else None
        ),
        "help": "Basé sur la moyenne depuis son premier squat",
    },
    {
        "label": "🕒 Dernière session loggée",
        "value": last_entry["name"] if last_entry is not None else "Aucun log",
        "delta": (
            f"{int(last_entry['squats'])} squats" if last_entry is not None else None
        ),
    },
]
render_metric_rows(pulse_metrics, per_row=1 if mobile_view else 3)

if not crew_daily_totals.empty:
    st.caption("Volume agrégé par jour (ligne pointillée = objectif collectif).")
    trend_fig = px.area(
        crew_daily_totals.tail(45),
        x="date_day",
        y="squats",
        title="Volume quotidien du crew",
        color_discrete_sequence=["#ff6f61"],
    )
    trend_fig.add_hline(
        y=len(participants) * SQUAT_JOUR,
        line_dash="dot",
        line_color="red",
        opacity=0.7,
    )
    trend_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Squats cumulés",
        margin=dict(l=10, r=10, t=60, b=20),
    )
    st.plotly_chart(trend_fig, use_container_width=True)


st.subheader("Qui a fait ses devoirs aujourd'hui ?")
devoirs = [
    f"✅ {participant.name} ({int(participant.sum_squats_done_today)} squats)"
    for participant in participants_obj.values()
    if participant.sum_squats_done_today >= SQUAT_JOUR
]
if devoirs:
    st.markdown("\n".join([f"- {entry}" for entry in devoirs]))
else:
    st.info("Personne n'a validé les 20 squats pour l'instant, qui s'y colle ?")

snapshot = []
for participant in participants_obj.values():
    snapshot.append(
        {
            "Squatteur": participant.name,
            "Aujourd'hui": int(participant.sum_squats_done_today),
            "Total": int(participant.sum_squats_done),
            "Delta vs obj": int(participant.delta_done_vs_objecitf_today),
            "Moyenne/jour": round(float(participant.moyenne_squats_par_jour), 2),
            "Streak (jours)": int(participant.current_objective_streak),
            "% objectif": round(float(participant.progress_pct_vs_objectif), 1),
        }
    )

leaderboard_df = pd.DataFrame(snapshot)
if not leaderboard_df.empty:
    leaderboard_df = leaderboard_df.sort_values("Total", ascending=False)
    st.subheader("Leaderboard du crew")
    st.dataframe(
        leaderboard_df,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Classement instantané, refresh auto quand une nouvelle session est enregistrée."
    )


# st.write("---")
# st.subheader("Focus par squatteur")

# focus_columns = 1 if mobile_view else 3
# for chunk_start in range(0, len(participant_order), focus_columns):
#     cols = st.columns(focus_columns)
#     for col, name in zip(
#         cols, participant_order[chunk_start : chunk_start + focus_columns]
#     ):
#         participant = participants_obj.get(name)
#         if participant is None or participant.df.empty:
#             col.info(f"{name} n'a pas encore loggé de squats.")
#             continue

#         with col:
#             st.markdown(f"### {name}")
#             st.metric(
#                 label="Aujourd'hui",
#                 value=int(participant.sum_squats_done_today),
#                 delta=int(participant.sum_squats_done_today - SQUAT_JOUR),
#             )
#             st.metric(
#                 label="Total cumulé",
#                 value=int(participant.sum_squats_done),
#                 delta=f"Depuis {participant.nombre_jours_depuis_debut} jours",
#             )
# st.metric(
#     label="Delta vs objectif",
#     value=int(participant.delta_done_vs_objecitf_today),
# )
# st.metric(
#     label="Moyenne / jour",
#     value=round(float(participant.moyenne_squats_par_jour), 2),
#     delta=round(float(participant.moyenne_squats_par_jour - SQUAT_JOUR), 2),
# # )
# st.metric(
#     label="🔥 Streak",
#     value=f"{participant.current_objective_streak} j",
#     delta=f"Record {participant.best_objective_streak}",
# )

# # progress_ratio = min(
# #     max(participant.sum_squats_done_today / SQUAT_JOUR, 0), 2
# # )
# # st.progress(
# #     min(progress_ratio, 1.0),
# #     text=(
# #         "Objectif du jour" if progress_ratio < 1 else "🔥 Objectif dépassé"
# #     ),
# # )

# st.caption(
#     f"{participant.sessions_logged} sessions • {participant.weekly_total} squats cette semaine"
# )

# if id_squatteur_from_cookies == name:
#     st.success(
#         "Connecté. Utilise le gros formulaire au-dessus pour logger."
#     )

st.write("---")

# add a comments at the bottom with the version of the app
st.caption(f"Version : 0.1.5 - time now = {today_date}")


if id_squatteur_from_cookies is not None and participant_obj is not None:
    today_snapshot = today.strftime("%Y-%m-%d")
    last_activity = (
        participant_obj.last_activity_date.strftime("%Y-%m-%d")
        if participant_obj.last_activity_date
        else "Jamais"
    )

    motivation_prompt = f""" Tu encourages {participant_obj.name} à faire des squats.

Contexte challenge : objectif {SQUAT_JOUR} squats/jour jusqu'au {end_of_year.strftime('%Y-%m-%d')} ({DAYS_LEFT} jours restants). Garder un ton punchy, sarcastique mais bienveillant, rappeler qu'on compte les reps pas les excuses.

Stats complètes (données figées au {today_snapshot} UTC+1) :
- Total cumulé : {int(participant_obj.sum_squats_done)} squats sur {participant_obj.sessions_logged} sessions.
- Aujourd'hui : {int(participant_obj.sum_squats_done_today)} squats (delta vs objectif = {int(participant_obj.sum_squats_done_today - SQUAT_JOUR)}).
- Hier : {int(participant_obj.sum_squats_hier)} squats.
- Delta annuel vs objectif : {int(participant_obj.delta_done_vs_objecitf_today)} squats.
- Progression annuelle : {participant_obj.progress_pct_vs_objectif:.1f}% | projection fin d'année = {participant_obj.projected_year_total} squats.
- Moyenne quotidienne : {participant_obj.moyenne_squats_par_jour:.2f} squats.
- Volume semaine courante : {participant_obj.weekly_total} squats (écart vs semaine précédente = {participant_obj.weekly_delta}).
- Streak actuel : {participant_obj.current_objective_streak} jours | Record : {participant_obj.best_objective_streak} jours.
- Dernière activité : {last_activity}.
- Objectif restant estimé : {participant_obj.objectif_sum_squat - participant_obj.sum_squats_done} squats pour boucler l'année.
"""

    message_motivation = mistral_chat(motivation_prompt)
    placeholder.markdown(message_motivation)
