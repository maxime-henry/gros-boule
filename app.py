from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_cookies_controller import CookieController





from motivation import motivate
from config import  load_all, today_data, mistral_chat, Participant, save_new_squat


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
DAYS_LEFT = (end_of_year - today).days + 1


data_total = load_all()
data_jour = today_data(data_total)



# --- Initialisation de st.session_state ---
today_date = today.date()  # Get today's date in UTC
# st.session_state.clear()
if "last_update" not in st.session_state :
    st.session_state.last_update = today_date  # Store the first update date


print(today_date)
print(st.session_state.last_update)


if "squat_data" not in st.session_state or st.session_state.last_update < today_date:
    st.session_state.squat_data = load_all()
    st.session_state.last_update = today_date  # Update the last update date

    st.session_state.participants_obj = {}
    for name in participants:
        st.session_state.participants_obj[name] = Participant(name, st.session_state.squat_data, days_left=DAYS_LEFT, squat_objectif_quotidien=SQUAT_JOUR)


# # Merge with a DataFrame containing all participants to ensure all participants are included
# df_participants = pd.DataFrame({'name': participants})
# df_all_participants_jour = pd.merge(df_participants, data_jour, on='name', how='left')
# # Set squats to 0 for participants without a value
# df_all_participants_jour['squats'].fillna(0, inplace=True)

# if st.button("Reset Session"):
#     st.session_state.clear()
#     st.rerun()  # Force the app to reload



# COOKIES CONTROL ##################################################################################################################
controller = CookieController()
cookies = controller.getAll()
id_squatteur_from_cookies = cookies.get("id_squatteur", None)
##################################################################################################################################### 

if id_squatteur_from_cookies is not None:



    participants= list(participants)
    participants.remove(id_squatteur_from_cookies)
    participants.insert(0, id_squatteur_from_cookies)
    
    st.title(f"Allez {id_squatteur_from_cookies}, t'es pas une merde!! ")
    
    participant_obj=st.session_state.participants_obj.get(id_squatteur_from_cookies)

    


    placeholder = st.empty()
    placeholder.info("Fait un squat en attendant au pire non ?")
    


    st.divider()



    st.write(f"{id_squatteur_from_cookies}, maintenant tu peux directement enregistrer tes squats ici :")

    with st.form("squat_form"):
        squats_faits = st.number_input(
            "Enregistrer une session squats :",
            min_value=5,
            max_value=600,
            value=20,
            step=1,
        )
        submitted = st.form_submit_button(f"Enregistrer pour {id_squatteur_from_cookies} 🍑")
    
    if submitted:
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
            participant_obj = st.session_state.participants_obj[id_squatteur_from_cookies] = Participant(
                id_squatteur_from_cookies,
                st.session_state.squat_data,
                days_left=DAYS_LEFT,
                squat_objectif_quotidien=SQUAT_JOUR
            )
            
            size = len(motivate)
            random_motivate = random.randrange(0, size)
            st.success(motivate[random_motivate])

            id_squatteur = id_squatteur_from_cookies
            controller.set("id_squatteur", id_squatteur, expires=datetime.now()+timedelta(days = 5, hours=1)) 


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

        with st.form(f"squat_form_tabs_{i}"):
            squats_faits = st.number_input(
                "Enregistrer une session squats :",
                min_value=5,
                max_value=600,
                value=20,
                step=1,
            )
            submitted = st.form_submit_button(f"Enregistrer pour {participants[i]} 🍑")
        
    
        valid = False
        if participants[i] == "Audrix":
            st.warning("Es-tu bien Audrix Cousinx ??")

            valid = st.checkbox("🚨 Oui, je suis AUDRIX !! 🚨", key= i+300)
        else:
            valid = True

        if submitted:
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
                controller.set("id_squatteur", id_squatteur, expires=datetime.now()+timedelta(days = 5, hours=1)) 

                st.toast("C'est enregistré frérot!", icon="🎉")
                st.rerun()
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


            if int(participant.delta_done_vs_objecitf_today) > 0:
                st.metric(label="Avance de squats", value= int(participant.delta_done_vs_objecitf_today))
            elif int(participant.delta_done_vs_objecitf_today) == 0:
                st.metric(label="Pile à l'équilibre", value= int(participant.delta_done_vs_objecitf_today))
            else :
                st.metric(label="Retard de squats", value= int(participant.delta_done_vs_objecitf_today))

            st.metric(label = "Squat moyen par jours", value=round(float(participant.moyenne_squats_par_jour),2), 
                    delta = round(float(participant.moyenne_squats_par_jour - SQUAT_JOUR ),2))


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
st.caption(f"Version : 0.1.4 - time now = {today_date}")

st.caption( st.session_state.last_update )

if id_squatteur_from_cookies is not None:
    message_motivation = mistral_chat(f"""{id_squatteur_from_cookies} a fait {participant_obj.sum_squats_done_today}  squat aujourd'hui 
                                    et {participant_obj.sum_squats_hier} hier. 
                                    Au global sur son objectif annuel {id_squatteur_from_cookies} à un différence de {participant_obj.delta_done_vs_objecitf_today} squats.
                                    {id_squatteur_from_cookies} à commence le challenge il y'a {participant_obj.nombre_jours_depuis_debut} et à une moyenne de {participant_obj.moyenne_squats_par_jour} squats par jour.""" )
    placeholder.text(message_motivation)


