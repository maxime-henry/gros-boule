import streamlit as st
from datetime import datetime
from structure import Personne
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import boto3
from boto3.dynamodb.conditions import Attr
import os
from dotenv import load_dotenv
load_dotenv()

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")



# Assuming you have AWS credentials set up or using other methods to authenticate with DynamoDB
table_squats = boto3.resource('dynamodb', region_name='eu-central-1' ,   aws_access_key_id= ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY).Table('squats')  # Replace with your DynamoDB table name




class Personne:
    def __init__(self, name,done, somme_squat):
        self.name = name
        self.done = done
        self.table = somme_squat
    


st.title("🍑 Squat app 🍑")
st.subheader("Une super app pour enregistrer vos squats")
st.write("Rappel : seuls les squats sont enregistrés (pas le fentes), minimum 10 squats d'affilés")

participants = ("Matix", "Max", "Floflox", "Audrix", "Vio")
objectif = 14200

# display the number of day between today and the end of the year
today = datetime.now()
end_of_year = datetime(today.year, 12, 31)
days_left = (end_of_year - today).days
squats_restant = days_left * 40

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Nombre de participants", value=len(participants))

with col2 :
    # metric nombre de jour restant
    st.metric(label="Jours restants", value=days_left)

with col3 :
    st.metric(label="Objectif du jour", value=squats_restant)
with col4 :
    st.metric(label="Objectif total", value=objectif, delta = "début 12 janvier", delta_color="off")
from collections import defaultdict

def load_data(name):
    result = table_squats.scan(FilterExpression=
        Attr('name').eq(name)
    )
    squats_by_day = defaultdict(int)
    for item in result['Items']:
        date = item['date'][:10]  # Extract only the date part
        squats_done = int(item['squats'])
        squats_by_day[date] += squats_done

    # Create a DataFrame
    df = pd.DataFrame(list(squats_by_day.items()), columns=['Date', 'Squats'])
    print(df)
    done = df['Squats'].sum()

    return Personne(name, done, df)

tabs  = st.tabs(participants)


for i, tab in enumerate(tabs):
    with tab :
        squats_faits =st.number_input(f"Enregistré une session squats", min_value=0, max_value=300, value=10, step=1, key = i+10)

        if st.button(f"🍑 Save 🍑", key= i):
            with st.spinner("Saving..."):
                User = load_data(participants[i])
                User.done += squats_faits
                st.success("Ton boule chamboule")

                table_squats.put_item(
                    Item={
                        'name': participants[i],
                        # date with time and seconds
                        "date": datetime.utcnow().isoformat() ,
                        'squats': squats_faits})

                st.toast("C'est enregistré mon reuf!", icon='🎉')
        st.write("---")
        
        User = load_data(participants[i])
        
        restant = objectif - User.done
        restant_jour = restant/days_left

                # Get today's date in the same format as your 'Date' column
        today_date = datetime.utcnow().strftime('%Y-%m-%d')

        # Filter DataFrame for today's date
        today_data = User.table[User.table['Date'] == today_date]

        # Calculate the sum of squats for today
        total_squats_today = today_data['Squats'].sum()


        col1,col2 = st.columns([2,5])
        with col1:
            st.metric(label="Squats restants", value=restant,delta=int(squats_restant-restant))
            st.metric(label="Total squats", value=User.done)
            # squat fait aujourd'hui 
            st.metric(label="Squats fait aujourd'hui", value=total_squats_today, delta = int(total_squats_today-40))
            
            # pourcentage de l'objectif rempli
            prct_objectif_rempli = round(100*User.done/objectif,2)
            st.metric(label="Pourcentage de l'objectif rempli", value = f"{prct_objectif_rempli}%")
            # nombre de squat moyen par jour

            mean_squat_per_day = round(User.table['Squats'].mean(),2)
            st.metric(label="Squat moyen par jour", value=mean_squat_per_day, delta=mean_squat_per_day-40)
            st.metric(label="Objectif squat/jour", value=round(restant_jour,2))
        with col2:



            # Plotly line chart
            fig = px.bar(User.table, x='Date', y='Squats', title='Nombre de squats')
            fig.update_layout(
                shapes=[
                    dict(
                        type='line',
                        yref='y',
                        y0=40,
                        y1=40,
                        xref='paper',  # Use 'paper' for x-axis values between 0 and 1
                        x0=0,
                        x1=1,
                        line=dict(color='red', width=2)
                    )
                ]
            )
          
            st.plotly_chart(fig, use_container_width=True)


        fig = px.box(User.table, x='Squats', title='Distribution des Squats')
        st.plotly_chart(fig, use_container_width=True)
