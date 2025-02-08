import os
from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_cookies_controller import CookieController





from motivation import motivate
from config import Personne, load_data, load_all, today_data, table_squats, mistral_chat


st.set_page_config(
    page_title="🍑 Squat app 🍑",
    page_icon="🍑",
    initial_sidebar_state="collapsed"
    
)

# LOAD and DEFINE the DATA here ######################################

participants = ("Audrix", "Matix", "Floflox", "Max", "Marinox",  "Viox", "Carlix", "Annax", "Elix", "Le K" , "Tonix","Fannux", "Thouvenix",)


SQUAT_JOUR = 20 

# display the number of day between today and the end of the year
today = datetime.now()+timedelta(hours=1)
end_of_year = datetime(today.year, 12, 31)
DAYS_LEFT = (end_of_year - today).days +1


data_total = load_all()
data_jour = today_data(data_total)


# Merge with a DataFrame containing all participants to ensure all participants are included
df_participants = pd.DataFrame({'name': participants})
df_all_participants_jour = pd.merge(df_participants, data_jour, on='name', how='left')
# Set squats to 0 for participants without a value
df_all_participants_jour['squats'].fillna(0, inplace=True)

data_hier = today_data(data_total, date = (datetime.now()+timedelta(days = -1, hours=1)).date())


# COOKIES CONTROL ##################################################################################################################
controller = CookieController()
cookies = controller.getAll()
id_squatteur_from_cookies = cookies.get("id_squatteur", None)
##################################################################################################################################### 

if id_squatteur_from_cookies is not None:
    
    st.title(f"Allez {id_squatteur_from_cookies}, t'es pas une merde!! ")
    
    squat_du_jour_participant = df_all_participants_jour[df_all_participants_jour["name"]==id_squatteur_from_cookies]
    valeur_squat_jour = squat_du_jour_participant["squats"].iloc[0] 

    squat_hier_participant = data_hier[data_hier["name"]==id_squatteur_from_cookies]
    valeur_squat_hier = squat_hier_participant["squats"].sum()


    message_motivation = mistral_chat(f"{id_squatteur_from_cookies} a fait {valeur_squat_jour}  squat aujourd'hui et {valeur_squat_hier} hier" )
    st.write(message_motivation)

    st.divider()

    st.write(f"{id_squatteur_from_cookies}, maintenant tu peux directement enregistrer tes squats ici :")

    squats_faits = st.number_input(
            f"Enregistrer une session squats :",
            min_value=5,
            max_value=600,
            value=20,
            step=1,
        )



    if st.button(f" Enregistrer pour {id_squatteur_from_cookies} 🍑") :
                with st.spinner("Saving..."):
                    # User = load_data(id_squatteur_from_cookies)
                    

                    size = len(motivate)
                    random_motivate = random.randrange(0, size)
                    st.success(motivate[random_motivate])

                    table_squats.put_item(
                        Item={
                            "name": id_squatteur_from_cookies,
                            # date with time and seconds
                            "date": (datetime.utcnow()+timedelta(hours=1)).isoformat(),
                            "squats": squats_faits,
                        }
                    )
                    id_squatteur = id_squatteur_from_cookies
                    controller.set("id_squatteur", id_squatteur) 

                    st.toast("C'est enregistré frérot!", icon="🎉")

    st.write("---")


else :
    st.title("🍑 Squat App 🍑")
    st.subheader("New year new me")
    st.write(
        "Cette année on se calme, objectif 20 squats par jour pendant un an"
    )
    st.caption("La persévérance, secret de tous les triomphes. - Victor Hugo")



col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Nombre de participants", value=len(participants))

with col2:
    # metric nombre de jour restant
    st.metric(label="Jours restants", value=DAYS_LEFT)

with col3:
    squats_restant = DAYS_LEFT * SQUAT_JOUR
    st.metric(label="Squats total restant", value=squats_restant, )

with col4:
    st.metric(
        label="Somme des squats fait",
        value=int(data_total["squats"].sum())
    )







st.write("Qui a fait ses devoirs ?")
# for each line of the data check if it more than SQUAT_JOUR
for index, row in df_all_participants_jour.iterrows():
    if row['squats'] >= SQUAT_JOUR:
        f"✅ {df_all_participants_jour.at[index, 'name']} 🍑"

st.divider()



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
        if participants[i] == "Audrix":
            st.warning("Es-tu bien Audrix Cousinx ??")

            valid = st.checkbox("🚨 Oui, je suis AUDRIX !! 🚨", key= i+300)
        else:
            valid = True

        if st.button(f"🍑 Enregistrer pour {participants[i]} 🍑", key= i) and valid :
            with st.spinner("Saving..."):
                # User = load_data(participants[i])
                User.done += squats_faits

                size = len(motivate)
                random_motivate = random.randrange(0, size)
                st.success(motivate[random_motivate])

                table_squats.put_item(
                    Item={
                        "name": participants[i],
                        # date with time and seconds
                        "date": (datetime.utcnow()+timedelta(hours=1)).isoformat(),
                        "squats": squats_faits,
                    }
                )
                id_squatteur = participants[i]
                controller.set("id_squatteur", id_squatteur) 

                st.toast("C'est enregistré frérot!", icon="🎉")
        st.write("---")

        # User = load_data(participants[i])
        

        restant = User.total_squat_challenge - User.done  # l'objectif doit etre changé ici 
        restant_jour = restant / DAYS_LEFT

        # Get today's date in the same format as your 'Date' column
        today_date = datetime.utcnow()+timedelta(hours=1)
        today_date = today_date.strftime("%Y-%m-%d")

        # Filter DataFrame for today's date
        today_data = User.table[User.table["Date"] == today_date]

        # Calculate the sum of squats for today
        total_squats_today = today_data["Squats"].sum()

        col1, col2 = st.columns([2, 5])
        with col1:
            # squat fait aujourd'hui
            st.metric(
                label="Squats fait aujourd'hui",
                value=total_squats_today,
                delta=int(total_squats_today - SQUAT_JOUR),
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
                delta=mean_squat_per_day - SQUAT_JOUR,
            )
            st.metric(label="Objectif squat/jour", value=round(restant_jour, 2))


            st.metric(label = "Squats à la fin de l'année", 
                      value = int(mean_squat_per_day*DAYS_LEFT+User.done),
                      delta = int(mean_squat_per_day*DAYS_LEFT+User.done) - User.total_squat_challenge)
        with col2:
            # Plotly line chart
            fig = px.bar(User.table, x="Date", y="Squats", title="Nombre de squats")
            fig.update_layout(
                shapes=[
                    {
                        "type":"line",
                        "yref":"y",
                        "y0":SQUAT_JOUR,
                        "y1":SQUAT_JOUR,
                        "xref":"paper",  # Use 'paper' for x-axis values between 0 and 1
                        "x0":0,
                        "x1":1,
                        "line":{"color":"red", "width":2}
                    }
                ]
            )

            st.plotly_chart(fig, use_container_width=True, key=i+1000)

        fig = px.box(User.table, x="Squats", title="Distribution des Squats")
        # st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# add a comments at the bottom with the version of the app 
st.caption(f"Version : 0.1.4 - time now = {today}")
