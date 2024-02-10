import streamlit as st
from config import load_all
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="🍑 Squat data 🍑",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
    
)


st.title("Tu veux de la data ?")
st.subheader("Curieux va")
st.write("---")

# I want this page to display the main stats and graphs 

df = load_all()
# order df my date as date time in this format 2024-01-17 08:49:32
df['date'] = pd.to_datetime(df['date'])
# change the date to only keep the day part
df['date_day'] = df['date'].dt.date
df = df.sort_values(by='date', ascending=False)
# a graph with the lines but empillé, summed one on top of the other
# Calculate cumulative sum of squats for each person
df['squats'] = pd.to_numeric(df['squats'])
df['cumulative_squats'] = df.groupby('name')['squats'].cumsum()

st.dataframe(df)

st.metric(label = "Nombre de sessions", value = len(df))
st.metric(label = "Nombre de participants", value = len(df['name'].unique()))
st.metric(label = "Nombre de squats", value = int(df['squats'].sum()))
# extract  the first row of the df

st.metric(label= "Dernière session", value = str(df[:1]["name"].value))