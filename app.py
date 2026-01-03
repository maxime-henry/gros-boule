from datetime import datetime, timedelta
import random
import streamlit as st
import plotly.express as px
import pandas as pd

from streamlit_cookies_controller import CookieController





from motivation import motivate
from config import  load_all, today_data, mistral_chat, Participant, save_new_squat, today, end_of_year


st.set_page_config(
    page_title="🍑 Squat app 🍑",
    page_icon="🍑",
    initial_sidebar_state="collapsed"
    
)

# LOAD and DEFINE the DATA here ######################################

participants = ("Audrix", "Matix", "Floflox", "Max", "Marinox",  "Viox", "Carlix", "Annax", "Elix", "Le K" , "Tonix","Fannux", "Thouvenix",)


SQUAT_JOUR = 20 

DAYS_LEFT = (end_of_year - today).days + 1


data_total = load_all()
# data_jour = today_data(data_total)



# --- Initialisation de st.session_state ---
today_date = today.date()  # Get today's date in UTC



squat_data = load_all()


participants_obj = {}
for name in participants:
    participants_obj[name] = Participant(name, squat_data, days_left=DAYS_LEFT, squat_objectif_quotidien=SQUAT_JOUR)





# COOKIES CONTROL ##################################################################################################################
controller = CookieController()
cookies = controller.getAll()
id_squatteur_from_cookies = cookies.get("id_squatteur", None)
##################################################################################################################################### 


def clear_login_cookie():
    """Reset the participant cookie so someone else can se connecter."""
    try:
        controller.delete("id_squatteur")  # type: ignore[attr-defined]
    except AttributeError:
        controller.set("id_squatteur", "", expires=datetime.now() - timedelta(days=1))


if id_squatteur_from_cookies is not None:



    participants= list(participants)
    participants.remove(id_squatteur_from_cookies)
    participants.insert(0, id_squatteur_from_cookies)
    
    st.title(f"Allez {id_squatteur_from_cookies}, t'es pas une merde!! ")

    if st.button("Pas toi ? Clique ici pour changer de squatteur", key="change_user_btn"):
        clear_login_cookie()
        st.rerun()
    
    participant_obj=participants_obj.get(id_squatteur_from_cookies)

    


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
            if squat_data is None or squat_data.empty:
                squat_data = new_entry_df
            else:
                squat_data = pd.concat(
                    [squat_data, new_entry_df], ignore_index=True
                )
            
            # Mettre à jour l'objet Participant correspondant
            participant_obj = participants_obj[id_squatteur_from_cookies] = Participant(
                id_squatteur_from_cookies,
                squat_data,
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

    st.subheader("Choisis ton blaze pour te connecter")
    st.caption("Clique sur ton nom, on te prépare le formulaire perso juste après 👇")
    selection_cols = st.columns(3)
    for idx, name in enumerate(participants):
        col = selection_cols[idx % len(selection_cols)]
        if col.button(f"{name} 🔓", key=f"login_{name}", use_container_width=True):
            controller.set(
                "id_squatteur",
                name,
                expires=datetime.now()+timedelta(days = 5, hours=1)
            )
            st.rerun()



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
for participant in participants_obj.values():
    # Check if the participant has met or exceeded the daily squat objective
    if participant.sum_squats_done_today >= SQUAT_JOUR:
        st.write(f"✅ {participant.name} 🍑")

st.divider()



tabs = st.tabs(participants)


for i, tab in enumerate(tabs):
    with tab:
        participant = participants_obj.get(participants[i])

        if participant is None:
            st.info("Aucune donnée pour ce squatteur pour le moment.")
            continue

        if id_squatteur_from_cookies == participants[i]:
            st.success("Tu es connecté ici, utilise le formulaire perso plus haut 👆")
        else:
            st.caption("Pour enregistrer tes squats, clique sur ton nom dans la zone de connexion au-dessus.")

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
st.caption(f"Version : 0.1.5 - time now = {today_date}")



if id_squatteur_from_cookies is not None:
    message_motivation = mistral_chat(f"""{id_squatteur_from_cookies} a fait {participant_obj.sum_squats_done_today}  squat aujourd'hui 
                                    et {participant_obj.sum_squats_hier} hier. 
                                    Au global sur son objectif annuel {id_squatteur_from_cookies} à un différence de {participant_obj.delta_done_vs_objecitf_today} squats.
                                    {id_squatteur_from_cookies} à commence le challenge il y'a {participant_obj.nombre_jours_depuis_debut} et à une moyenne de {participant_obj.moyenne_squats_par_jour} squats par jour.""" )
    placeholder.text(message_motivation)


