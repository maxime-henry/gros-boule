import streamlit as st
from config import load_all
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="🍑 Squat stat 🍑",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
    
)


st.title("Plus de stASStistique")
st.write("---")

# I want this page to display the main stats and graphs 

df = load_all()
# order df my date as date time in this format 2024-01-17 08:49:32
df['date'] = pd.to_datetime(df['date'])
# change the date to only keep the day part
df['date_day'] = df['date'].dt.date
df = df.sort_values(by='date_day')

# a graph with the lines but empillé, summed one on top of the other
# Calculate cumulative sum of squats for each person
df['squats'] = pd.to_numeric(df['squats'])
df['cumulative_squats'] = df.groupby('name')['squats'].cumsum()



# Find the person who usually makes the first squats of the day
first_squats = df.loc[df.groupby(df['date_day'])['date'].idxmin()]

# Find the person who usually makes the last squats of the day
last_squats = df.loc[df.groupby(df['date'].dt.date)['date'].idxmax()]



squatteur_du_matin = first_squats["name"].mode()[0]
squatteur_du_soir = last_squats["name"].mode()[0]

first_squats = first_squats[first_squats["name"]==squatteur_du_matin]
last_squats = last_squats[last_squats["name"]==squatteur_du_soir]

# Calculate metrics for histogram
max_squats = df['squats'].max()
min_squats = df['squats'].min()

person_most_squats = df.loc[df['squats'] == max_squats, 'name'].iloc[0]
person_least_squats = df.loc[df['squats'] == min_squats, 'name'].iloc[0]



st.metric(label=f"Record du plus de squats en une session 👏", value=person_most_squats, delta = int(max_squats))



fig = px.histogram(data_frame=df, x="squats", title="Distribution des Squats")
fig.update_layout(
    xaxis_title="Squats",
    yaxis_title="Nombre de sessions")
st.plotly_chart(fig)
st.write("---")

# Line plot of squats over time for each person
# and smooth the lines 
st.metric(label="⏰ Squatteur le plus matinal :", value= squatteur_du_matin, delta = f"le plus tôt : {first_squats['date'].min().strftime('%H:%M:%S')}", delta_color="off")
st.metric(label="🌙 Squatteur du soir :", value= squatteur_du_soir, delta = f"le plus tard : {last_squats['date'].max().strftime('%H:%M:%S')}", delta_color="off")

st.write("---")
fig = px.line(data_frame=df, x="date_day", y="squats", color="name", title="📈 Evolution des squats", line_shape='spline')
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Squats",
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
    ])
st.plotly_chart(fig)



# Plot stacked lines
fig = px.area(data_frame=df, x = "date_day", y = "cumulative_squats", line_group="name", color="name", title=" Squats CULmulés")
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Squats")
st.plotly_chart(fig)



# Scatter plot of squats over time colored by person
fig = px.scatter(data_frame=df, x="date_day", y="squats", color="name", title="Ce graph est cool non ?")
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Squats",
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
    ])
st.plotly_chart(fig)

consistent_squatter = df.groupby('name')['squats'].std().idxmin()
least_consistent_squatter = df.groupby('name')['squats'].std().idxmax()
average_squats_per_session = df.groupby('name')['squats'].mean()
total_sessions = df.groupby('name')['date_day'].nunique()


# Display additional metrics
st.write("---")

st.metric(label="🎲 Squatteur le plus régulier :", value=str(consistent_squatter), delta=df.groupby('name')['squats'].std().min())
st.metric(label="🎲 Squatteur le plus random :", value=str(least_consistent_squatter), delta=df.groupby('name')['squats'].std().max())

# Box plot of squats distribution across people
fig = px.box(data_frame=df, x="name", y="squats", title="📊 Distribution des squats par jours")
fig.update_layout(
    xaxis_title="Qui ?",
    yaxis_title="Squats",
    
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
    ])
st.plotly_chart(fig)

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
st.write("---")
# Name with max sum of squats and sum of squats
person_max_sum = df.groupby('name')['squats'].sum().idxmax()
person_min_sum = df.groupby('name')['squats'].sum().idxmin()
sum_squats = df['squats'].sum()
st.metric(label="Qui a fait le plus de squats ?", value=person_max_sum, delta=f"{int(df.groupby('name')['squats'].sum().max())} gros squats")
st.metric(label="Somme des squats de l'équipe", value=int(sum_squats))
st.metric(label="Qui a fait le moins de squats ?", value=person_min_sum, delta=f"{int(df.groupby('name')['squats'].sum().min())} squats, lâche rien mon reuf", delta_color="inverse")

# Pie chart of proportion of squats done by each person
fig = px.pie(data_frame=df, names="name", values="squats", title="🍑 Proportion des squats par squatteur : ")
st.plotly_chart(fig)

# Bar chart of total squats done by each person
total_squats = df.groupby("name")["squats"].sum().reset_index()
# order the bars
total_squats = total_squats.sort_values(by="squats", ascending=False)
fig = px.bar(total_squats, x="name", y="squats", title="Somme des squats par participant")
fig.update_layout(
    # hide x label 
    xaxis_title=None,



    yaxis_title="Squats",
    
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
    ])
st.plotly_chart(fig)


