from datetime import datetime, timedelta, timezone
import os
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
    get_today,
    get_end_of_year,
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
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .section-header .emoji {
        font-size: 1.5rem;
    }
    .section-card {
        background: rgba(255,255,255,0.7);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,111,97,0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,111,97,0.3), transparent);
        margin: 1.5rem 0;
    }
    .badge-success {
        background: #d4edda;
        color: #155724;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-warning {
        background: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Custom background for bordered containers */
    div[data-testid="stVerticalBlock"] {
        /*background: rgba(255, 255, 255, 0.7) !important;*/
        border-radius: 16px !important;
        border: 1px solid rgba(255, 111, 97, 0.2) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08) !important;
        padding: 1.5rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        background: transparent !important;
    }

    /* Radial progress ring styles */
    .radial-progress {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1rem;
    }
    .radial-progress svg {
        transform: rotate(-90deg);
        filter: drop-shadow(0 4px 12px rgba(255, 111, 97, 0.3));
    }
    .radial-progress .ring-bg {
        fill: none;
        stroke: rgba(255, 111, 97, 0.15);
    }
    .radial-progress .ring-progress {
        fill: none;
        stroke: url(#peachGradient);
        stroke-linecap: round;
        transition: stroke-dashoffset 0.6s ease;
    }
    .radial-progress .ring-label {
        position: absolute;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .radial-progress .ring-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ff6f61;
    }
    .radial-progress .ring-subtitle {
        font-size: 0.75rem;
        color: #666;
        margin-top: 2px;
    }
    .radial-container {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
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

# Compute today and end_of_year fresh on each run
today = get_today()
end_of_year = get_end_of_year()

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


def render_radial_progress(
    percent: float, label: str, subtitle: str = "", size: int = 140, stroke: int = 10
):
    """Render a radial progress ring with gradient fill."""
    # Clamp percent between 0 and 100 for display, but show actual value
    display_percent = min(max(percent, 0), 100)
    radius = (size - stroke) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - display_percent / 100)

    html = f"""
    <div class="radial-progress">
        <div class="radial-container" style="width:{size}px;height:{size}px;">
            <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <defs>
                    <linearGradient id="peachGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#ff6f61;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#ff8a65;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#ffab91;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <circle class="ring-bg" cx="{size/2}" cy="{size/2}" r="{radius}" stroke-width="{stroke}"/>
                <circle class="ring-progress" cx="{size/2}" cy="{size/2}" r="{radius}" 
                    stroke-width="{stroke}" 
                    stroke-dasharray="{circumference}" 
                    stroke-dashoffset="{offset}"/>
            </svg>
            <div class="ring-label" style="width:{size}px;height:{size}px;">
                <span class="ring-value">{label}</span>
                <span class="ring-subtitle">{subtitle}</span>
            </div>
        </div>
    </div>
    """
    return html


# @st.cache_data(ttl=100, max_entries=1)
def chat_with_mistral(prompt: str, name: str) -> str:
    """Helper to chat with Mistral model."""
    response = mistral_chat(prompt)
    return response


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


# COOKIES CONTROL ##################################################################################################################
controller = CookieController(key="squat_cookies")

# Give cookies-controller time to load; fallback to session_state
if "id_squatteur" not in st.session_state:
    st.session_state["id_squatteur"] = None
if "pending_loading" not in st.session_state:
    st.session_state["pending_loading"] = None


if st.session_state.get("pending_loading"):
    if st.session_state["pending_loading"] == "LOGOUT":
        controller.remove("id_squatteur")
        st.session_state["id_squatteur"] = None
    else:
        controller.set("id_squatteur", st.session_state["pending_loading"])

    st.session_state["pending_loading"] = None


try:
    cookies = controller.getAll() or {}
except Exception:
    cookies = {}

if cookies.get("id_squatteur"):
    st.session_state["id_squatteur"] = cookies.get("id_squatteur")

active_user = st.session_state.get("id_squatteur")
#####################################################################################################################################


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


participant_order = list(participants)
participant_obj = participants_obj.get(active_user) if active_user else None


is_logged_in = active_user in participants_obj

if not is_logged_in:
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
        if col.button(f"{name} 🔓", key=f"login_{name}", width="stretch"):

            st.session_state["pending_loading"] = name
            st.rerun()
    login_container.markdown("</div>", unsafe_allow_html=True)


if is_logged_in:
    # Keep the active user first in displays.
    participant_order = list(participants)
    if active_user in participant_order:
        participant_order.remove(active_user)
        participant_order.insert(0, active_user)

    st.title(f"Allez {active_user}, t'es pas une merde!! ")

    if st.button(
        "Pas toi ? Clique ici pour changer de squatteur", key="change_user_btn"
    ):
        # clear_login_cookie()
        st.session_state["pending_loading"] = "LOGOUT"
        active_user = None
        is_logged_in = False
        participant_obj = None
        st.rerun()

    placeholder = st.empty()

    st.divider()

    st.write(
        f"{active_user}, maintenant tu peux directement enregistrer tes squats ici :"
    )

    with st.form("squat_form"):
        squats_faits = st.number_input(
            "Enregistrer une session squats :",
            min_value=5,
            max_value=600,
            value=20,
            step=1,
        )
        submitted = st.form_submit_button(f"Enregistrer pour {active_user} 🍑")

    if submitted:
        with st.spinner("Saving..."):
            # Sauvegarder dans DynamoDB
            new_item = save_new_squat(active_user, squats_faits)

            refresh_squat_dataframe()
            participant_obj = participants_obj[active_user] = Participant(
                active_user,
                fetch_squat_dataframe(),
                days_left=DAYS_LEFT,
                squat_objectif_quotidien=SQUAT_JOUR,
            )

            size = len(motivate)
            random_motivate = random.randrange(0, size)
            st.success(motivate[random_motivate])

            st.rerun()

    if participant_obj is not None:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header"><span class="emoji">🎯</span><h3 style="margin:0">Ton tableau de bord</h3></div>',
            unsafe_allow_html=True,
        )
        st.caption("Tes stats personnelles en temps réel")

        # Radial progress rings for daily and annual goals
        with st.container(border=True):
            daily_pct = (participant_obj.sum_squats_done_today / SQUAT_JOUR) * 100
            annual_pct = participant_obj.progress_pct_vs_objectif

            if mobile_view:
                ring_cols = [st.container(), st.container()]
            else:
                ring_cols = st.columns(2)

            with ring_cols[0]:
                st.markdown(
                    render_radial_progress(
                        daily_pct,
                        f"{int(participant_obj.sum_squats_done_today)}",
                        f"/ {SQUAT_JOUR} aujourd'hui",
                        size=130,
                        stroke=12,
                    ),
                    unsafe_allow_html=True,
                )
            with ring_cols[1]:
                st.markdown(
                    render_radial_progress(
                        annual_pct,
                        f"{annual_pct:.1f}%",
                        "objectif annuel",
                        size=130,
                        stroke=12,
                    ),
                    unsafe_allow_html=True,
                )

        with st.container(border=True):
            cockpit_metrics = [
                {
                    "label": "Total cumulé",
                    "value": int(participant_obj.sum_squats_done),
                },
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

        st.markdown(
            '<div class="section-header"><span class="emoji">🔥</span><h4 style="margin:0">Régularité & Streaks</h4></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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

        st.markdown(
            '<div class="section-header"><span class="emoji">📊</span><h4 style="margin:0">Tendances</h4></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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
            ]
            render_metric_rows(trend_metrics, per_row=1 if mobile_view else 2)

        with st.container(border=True):
            st.progress(
                min(participant_obj.progress_pct_vs_objectif / 100, 1.0),
                text="Progression sur l'objectif annuel",
            )
            st.caption(
                "Barre verte = ton pourcentage du défi annuel. Continue d'empiler."
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header"><span class="emoji">📈</span><h4 style="margin:0">Historique des sessions</h4></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
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
            # Apply gradient-like coloring based on values
            fig.update_traces(
                marker=dict(
                    color=personal_history["squats"],
                    colorscale=[[0, "#ffab91"], [0.5, "#ff8a65"], [1, "#ff6f61"]],
                    line=dict(width=0),
                ),
                opacity=0.9,
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
                        "line": {"color": "#e53935", "width": 2, "dash": "dot"},
                    }
                ],
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor="rgba(255,111,97,0.1)")
            st.plotly_chart(fig, width="stretch")

        with box_col:
            pass
            # box_fig = px.box(personal_history, y="squats", title="Distribution")
            # st.plotly_chart(box_fig, width="stretch")


elif not is_logged_in:
    # Login UI already rendered above.
    pass


st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-header"><span class="emoji">🏆</span><h3 style="margin:0">Challenge Collectif 2026</h3></div>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    if mobile_view:
        hero_cols = [st.container(), st.container()]
    else:
        hero_cols = st.columns([2, 1])
    with hero_cols[0]:
        st.markdown(
            "**🎯 L'objectif :** 20 squats par jour, chaque jour, jusqu'au 31 décembre."
        )
        st.caption("On compte les reps, pas les excuses.")
        st.metric(
            label="Squats cumulés",
            value=f"{crew_total_squats:,}".replace(",", " "),
            delta=f"{crew_delta_today:+d} vs objectif",
        )
    with hero_cols[1]:
        st.markdown(
            render_radial_progress(
                crew_completion_pct,
                f"{crew_completion_pct:.1f}%",
                "challenge complété",
                size=120,
                stroke=10,
            ),
            unsafe_allow_html=True,
        )

    crew_metrics = [
        {
            "label": "Team en piste",
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

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-header"><span class="emoji">⚡</span><h3 style="margin:0">Highlights du jour</h3></div>',
    unsafe_allow_html=True,
)
st.caption("Qui brille aujourd'hui dans l'équipe ?")
with st.container(border=True):
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
                f"{int(last_entry['squats'])} squats"
                if last_entry is not None
                else None
            ),
        },
    ]
    render_metric_rows(pulse_metrics, per_row=1 if mobile_view else 3)

if not crew_daily_totals.empty:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="emoji">📊</span><h3 style="margin:0">Volume quotidien</h3></div>',
        unsafe_allow_html=True,
    )
    st.caption("Squats cumulés par jour · La ligne rouge = objectif collectif")
    with st.container(border=True):
        trend_fig = px.area(
            crew_daily_totals.tail(45),
            x="date_day",
            y="squats",
            title="Volume quotidien du crew",
        )
        # Apply gradient fill effect
        trend_fig.update_traces(
            fill="tozeroy",
            fillgradient=dict(
                type="vertical",
                colorscale=[
                    [0, "rgba(255,171,145,0.1)"],
                    [0.5, "rgba(255,138,101,0.4)"],
                    [1, "rgba(255,111,97,0.8)"],
                ],
            ),
            line=dict(color="#ff6f61", width=3),
        )
        trend_fig.add_hline(
            y=len(participants) * SQUAT_JOUR,
            line_dash="dot",
            line_color="#e53935",
            opacity=0.8,
            annotation_text=f"Objectif ({len(participants) * SQUAT_JOUR})",
            annotation_position="top right",
        )
        trend_fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Squats cumulés",
            margin=dict(l=10, r=10, t=60, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        trend_fig.update_xaxes(showgrid=False)
        trend_fig.update_yaxes(showgrid=True, gridcolor="rgba(255,111,97,0.1)")
        st.plotly_chart(trend_fig, width="stretch")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-header"><span class="emoji">✅</span><h3 style="margin:0">Devoirs du jour</h3></div>',
    unsafe_allow_html=True,
)
st.caption("Qui a validé ses 20 squats aujourd'hui ?")
with st.container(border=True):
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
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="emoji">🏅</span><h3 style="margin:0">Classement</h3></div>',
        unsafe_allow_html=True,
    )
    st.caption("Qui mène la danse ?")
    with st.container(border=True):
        st.dataframe(
            leaderboard_df,
            # width="stretch",
            hide_index=True,
        )
        st.caption("Mise à jour automatique à chaque nouvelle session.")


st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.caption(f"🍑 Squat App v0.1.6 · {today.strftime('%d/%m/%Y-%H:%M')}")


if active_user is not None and participant_obj is not None:
    today_snapshot = today.strftime("%Y-%m-%d")
    last_activity = (
        participant_obj.last_activity_date.strftime("%Y-%m-%d")
        if participant_obj.last_activity_date
        else "Jamais"
    )

    motivation_prompt = f""" Tu encourages {participant_obj.name} à faire des squats.

Contexte challenge : objectif {SQUAT_JOUR} squats/jour jusqu'au {end_of_year.strftime('%Y-%m-%d')} ({DAYS_LEFT} jours restants). 

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
- Squats des autres membres aujourd'hui : {active_today} sur {len(participants)} ont déjà validé leurs {SQUAT_JOUR} squats.
"""

    # message_motivation = mistral_chat(motivation_prompt)

    placeholder.markdown(chat_with_mistral(motivation_prompt, participant_obj.name))
