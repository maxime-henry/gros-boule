import os
from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_cookies_controller import CookieController





from motivation import motivate
from config import Personne, load_data, load_all, today_data, table_squats, mistral_chat, Participant, save_new_squat


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


# --- Initialisation de st.session_state ---
if "squat_data" not in st.session_state:
    st.session_state.squat_data = load_all()

if "participants_obj" not in st.session_state:
    st.session_state.participants_obj = {}
    for name in participants:
        st.session_state.participants_obj[name] = Participant(name, st.session_state.squat_data, days_left=DAYS_LEFT, squat_objectif_quotidien=SQUAT_JOUR)


# Merge with a DataFrame containing all participants to ensure all participants are included
df_participants = pd.DataFrame({'name': participants})
df_all_participants_jour = pd.merge(df_participants, data_jour, on='name', how='left')
# Set squats to 0 for participants without a value
df_all_participants_jour['squats'].fillna(0, inplace=True)




# COOKIES CONTROL ##################################################################################################################
controller = CookieController()
cookies = controller.getAll()
id_squatteur_from_cookies = cookies.get("id_squatteur", None)
##################################################################################################################################### 

if id_squatteur_from_cookies is not None:
    
    st.title(f"Allez {id_squatteur_from_cookies}, t'es pas une merde!! ")
    
    participant_obj=st.session_state.participants_obj.get(id_squatteur_from_cookies)



    message_motivation = mistral_chat(f"{id_squatteur_from_cookies} a fait {participant_obj.sum_squats_done_today}  squat aujourd'hui et {participant_obj.sum_squats_hier} hier" )
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
    
    if st.button(f"Enregistrer pour {id_squatteur_from_cookies} 🍑"):
        with st.spinner("Saving..."):
            # Sauvegarder dans DynamoDB
            new_item = save_new_squat(id_squatteur_from_cookies, squats_faits)
            
            # Mettre à jour la copie locale des données
            new_entry_df = pd.DataFrame([new_item])
            if st.session_state.squat_data is None or st.session_state.squat_data.empty:
                st.session_state.squat_data = new_entry_df
            else:
                st.session_state.squat_data = pd.concat(
                    [st.session_state.squat_data, new_entry_df], ignore_index=True
                )
            
            # Mettre à jour l'objet Participant correspondant
            st.session_state.participants_obj[id_squatteur_from_cookies] = Participant(
                id_squatteur_from_cookies,
                st.session_state.squat_data,
                days_left=DAYS_LEFT,
                squat_objectif_quotidien=SQUAT_JOUR
            )
            
            size = len(motivate)
            random_motivate = random.randrange(0, size)
            st.success(motivate[random_motivate])


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
# Iterate over all Participant objects stored in session_state
for participant in st.session_state.participants_obj.values():
    # Check if the participant has met or exceeded the daily squat objective
    if participant.sum_squats_done_today >= SQUAT_JOUR:
        st.write(f"✅ {participant.name} 🍑")

st.divider()



tabs = st.tabs(participants)


for i, tab in enumerate(tabs):
    with tab:

        # User = st.session_state.participants_obj.get(participants[i])

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

        if st.button(f"Enregistrer pour {participants[i]} 🍑", key = i*4500):
            with st.spinner("Saving..."):
                # Sauvegarder dans DynamoDB
                new_item = save_new_squat(participants[i], squats_faits)
                
                # Mettre à jour la copie locale des données
                new_entry_df = pd.DataFrame([new_item])
                if st.session_state.squat_data is None or st.session_state.squat_data.empty:
                    st.session_state.squat_data = new_entry_df
                else:
                    st.session_state.squat_data = pd.concat(
                        [st.session_state.squat_data, new_entry_df], ignore_index=True
                    )
                
                # Mettre à jour l'objet Participant correspondant
                st.session_state.participants_obj[participants[i]] = Participant(
                    participants[i],
                    st.session_state.squat_data,
                    days_left=DAYS_LEFT,
                    squat_objectif_quotidien=SQUAT_JOUR
                )
                
                size = len(motivate)
                random_motivate = random.randrange(0, size)
                st.success(motivate[random_motivate])
                id_squatteur = participants[i]
                controller.set("id_squatteur", id_squatteur) 

                st.toast("C'est enregistré frérot!", icon="🎉")
        st.write("---")

        

        participant = st.session_state.participants_obj.get(participants[i])

        col1, col2 = st.columns([2, 5])
        with col1:
            # squat fait aujourd'hui
            st.metric(
                label="Squats fait aujourd'hui",
                value=int(participant.sum_squats_done_today),
                delta=int(participant.sum_squats_done_today - SQUAT_JOUR),
            )


            st.metric(label="Total squats fait", value= int(participant.sum_squats_done),
                      delta=f"En {participant.nombre_jours_depuis_debut} jours")

            st.metric(label="Retard de squats", value= int(participant.delta_done_vs_objecitf_today))

        with col2:
            # Plotly line chart
            fig = px.bar(participant.df, x="date", y="squats", title="Nombre de squats")
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

        fig = px.box(participant.df, x="squats", title="Distribution des Squats")
        # st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# add a comments at the bottom with the version of the app 
st.caption(f"Version : 0.1.4 - time now = {today}")
