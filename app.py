
from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from motivation import motivate
from config import Personne, load_data, load_all, today_data, table_squats



st.set_page_config(
    page_title="🍑 Squat app 🍑",
    page_icon="🍑",
    initial_sidebar_state="collapsed"
    
)


st.title("🍑 Squat app 🍑")
st.subheader("Une super app pour enregistrer vos squats!")
st.write(
    "Rappel : seuls les squats sont enregistrés (pas les fentes), minimum 10 squats d'affilés"
)

participants = ("Matix", "Max", "Floflox", "Audrix", "Viox", "Carlix", "Elix", "Tonix","Fannux", "Annax", "Thouvenix", "Marinox")
OBJECTIF = 14160

# display the number of day between today and the end of the year
today = datetime.now()+timedelta(hours=2)
end_of_year = datetime(today.year, 12, 31)
days_left = (end_of_year - today).days
squats_restant = days_left * 40

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Nombre de participants", value=len(participants))

with col2:
    # metric nombre de jour restant
    st.metric(label="Jours restants", value=days_left)

with col3:
    st.metric(label="Squats total restant", value=squats_restant, )

data_total = load_all()
with col4:
    st.metric(
        label="Somme des squats fait",
        value=int(data_total["squats"].sum())
    )


data_jour = today_data()
# Merge with a DataFrame containing all participants to ensure all participants are included
df_all_participants = pd.DataFrame({'name': participants})
df = pd.merge(df_all_participants, data_jour, on='name', how='left')
# Set squats to 0 for participants without a value
df['squats'].fillna(0, inplace=True)


fig = px.bar(df, x="name", y="squats" , title="Qui a fait ses devoirs ?", height=350)
fig.update_layout(
    xaxis={'categoryorder':'array', 'categoryarray':participants, "autorange": True},

    shapes=[
        {
            "type":"line",
            "yref":"y",
            "y0":40,
            "y1":40,
            "xref":"paper",  # Use 'paper' for x-axis values between 0 and 1
            "x0":0,
            "x1":1,
            "line":{"color":"red", "width":2}
        }
    ]
)
fig.update_layout(
    
    xaxis=dict(title="Participants"),
    yaxis=dict(title="Nombre de squats")
)


st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})


tabs = st.tabs(participants)


for i, tab in enumerate(tabs):
    with tab:

        User = load_data(participants[i])

        squats_faits = st.number_input(
            f"Enregistrer une session squats",
            min_value=5,
            max_value=600,
            value=20,
            step=1,
            key=i + 50,
        )

        valid = False
        if participants[i] == "Matix":
            st.warning("Es-tu bien Matix Bartz ??")

            valid = st.checkbox("🚨 Oui, je suis MATIX !! 🚨", key= i+300)
            st.info("Il est interdit de voler l'identité d'autrui.")
        else:
            valid = True

        if st.button(f"🍑 Save pour {participants[i]} 🍑", key= i) and valid :
            with st.spinner("Saving..."):
                User = load_data(participants[i])
                User.done += squats_faits

                size = len(motivate)
                random_motivate = random.randrange(0, size)
                st.success(motivate[random_motivate])

                table_squats.put_item(
                    Item={
                        "name": participants[i],
                        # date with time and seconds
                        "date": (datetime.utcnow()+timedelta(hours=2)).isoformat(),
                        "squats": squats_faits,
                    }
                )

                st.toast("C'est enregistré mon reuf!", icon="🎉")
        st.write("---")

        User = load_data(participants[i])
        

        restant = User.total_squat_challenge - User.done  # l'objectif doit etre changé ici 
        restant_jour = restant / days_left

        # Get today's date in the same format as your 'Date' column
        today_date = datetime.utcnow()+(hours=2)
        today_date = today_date.strftime("%Y-%m-%d")

        # Filter DataFrame for today's date
        today_data = User.table[User.table["Date"] == today_date]

        # Calculate the sum of squats for today
        total_squats_today = today_data["Squats"].sum()
        #if total_squats_today >= 40:
            #st.toast(f"Bravo {participants[i]}! Objectif atteint!!! ", icon = "😍")

        col1, col2 = st.columns([2, 5])
        with col1:
            # squat fait aujourd'hui
            st.metric(
                label="Squats fait aujourd'hui",
                value=total_squats_today,
                delta=int(total_squats_today - 40),
            )

            st.metric(
                label="Squats restants",
                value=restant,
                delta=int(squats_restant - restant),
            )

            st.metric(
                label = "Objectif total",
                value = User.total_squat_challenge,
                delta=f"debut {str(User.earliest_date.strftime('%d %B'))}",
                delta_color="off"
            )

            st.metric(label="Total squats fait", value=User.done)


            # pourcentage de l'objectif rempli
            prct_objectif_rempli = round(100 * User.done / User.total_squat_challenge, 2)
            st.metric(
                label="Pourcentage de l'objectif rempli",
                value=f"{prct_objectif_rempli}%",
            )
            # nombre de squat moyen par jour
            # nombre de jour depuis le debut du challenge du participant
            nb_jour_defi = (today.date() - User.earliest_date).days + 1

            mean_squat_per_day = round(User.table["Squats"].sum() / nb_jour_defi, 2)
            st.metric(
                label="Squat moyen fait par jour",
                value=mean_squat_per_day,
                delta=mean_squat_per_day - 40,
            )
            st.metric(label="Objectif squat/jour", value=round(restant_jour, 2))


            st.metric(label = "Squats à la fin de l'année", 
                      value = int(mean_squat_per_day*days_left+User.done),
                      delta = int(mean_squat_per_day*days_left+User.done) - User.total_squat_challenge)
        with col2:
            # Plotly line chart
            fig = px.bar(User.table, x="Date", y="Squats", title="Nombre de squats")
            fig.update_layout(
                shapes=[
                    {
                        "type":"line",
                        "yref":"y",
                        "y0":40,
                        "y1":40,
                        "xref":"paper",  # Use 'paper' for x-axis values between 0 and 1
                        "x0":0,
                        "x1":1,
                        "line":{"color":"red", "width":2}
                    }
                ]
            )

            st.plotly_chart(fig, use_container_width=True)

        fig = px.box(User.table, x="Squats", title="Distribution des Squats")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# add a comments at the bottom with the version of the app 
st.caption(f"Version : 0.1.3 - time now = {today}")
