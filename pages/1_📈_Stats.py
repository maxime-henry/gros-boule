import streamlit as st
from config import load_all
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="🍑 Squat stat 🍑",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.title("Plus de stASStistique")
st.write("---")

# I want this page to display the main stats and graphs

df = load_all()
# order df my date as date time in this format 2024-01-17 08:49:32
df["date"] = pd.to_datetime(df["date"])
# change the date to only keep the day part
df["date_day"] = df["date"].dt.date
df = df.sort_values(by="date")


# a graph with the lines but empillé, summed one on top of the other
# Calculate cumulative sum of squats for each person
df["squats"] = pd.to_numeric(df["squats"])
df["cumulative_squats"] = df.groupby("name")["squats"].cumsum()

daily_squats = df.groupby(["date_day", "name"])["squats"].sum().reset_index()
daily_squats["cumulative_squats"] = daily_squats.groupby("name")["squats"].cumsum()



# Create a pivot table to reshape the DataFrame
pivot_df = daily_squats.pivot_table(index='date_day', columns='name', values='squats', aggfunc='sum', fill_value=0)

# Reset index to make 'date' a column again (optional)
pivot_df = pivot_df.reset_index()

result_df = pivot_df.melt(id_vars="date_day")

result_df.columns = ['date_day', "name", "squats"]

# Initialize an empty DataFrame to store the filtered rows
filtered_df = pd.DataFrame(columns=result_df.columns)
# Iterate over unique names
for name in result_df['name'].unique():
    # Filter rows for the current name
    name_df = result_df[result_df['name'] == name].reset_index(drop=True)
    
    # Find the first index with non-zero squats
    first_non_zero_index = name_df['squats'].gt(0).idxmax()
    
    # Filter rows after the first non-zero squats recording
    name_filtered_df = name_df.loc[first_non_zero_index:].reset_index(drop=True)
    
    # Append the filtered rows to the overall filtered DataFrame
    filtered_df = pd.concat([filtered_df, name_filtered_df], ignore_index=True)

# Display the result
filtered_df = filtered_df.sort_values(by="date_day")

# Find the person who usually makes the first squats of the day
first_squats = df.loc[df.groupby(df["date_day"])["date"].idxmin()]

# Find the person who usually makes the last squats of the day
last_squats = df.loc[df.groupby(df["date"].dt.date)["date"].idxmax()]


squatteur_du_matin = first_squats["name"].mode()[0]
squatteur_du_soir = last_squats["name"].mode()[0]

first_squats = first_squats[first_squats["name"] == squatteur_du_matin]
last_squats = last_squats[last_squats["name"] == squatteur_du_soir]

# Calculate metrics for histogram
max_squats = df["squats"].max()
min_squats = df["squats"].min()

person_most_squats = df.loc[df["squats"] == max_squats, "name"].iloc[0]
person_least_squats = df.loc[df["squats"] == min_squats, "name"].iloc[0]


st.metric(
    label=f"Record du plus de squats en une session 👏",
    value=person_most_squats,
    delta=int(max_squats),
)


fig = px.histogram(data_frame=df, x="squats", title="Distribution des Squats", nbins=50)
fig.update_layout(xaxis_title="Squats", yaxis_title="Nombre de sessions")
st.plotly_chart(fig, use_container_width=True)
st.write("---")

# Line plot of squats over time for each person
# and smooth the lines
st.metric(
    label="⏰ Squatteur le plus matinal :",
    value=squatteur_du_matin,
    delta=f"le plus tôt : {first_squats['date'].min().strftime('%H:%M:%S')}",
    delta_color="off",
)
st.metric(
    label="🌙 Squatteur du soir :",
    value=squatteur_du_soir,
    delta=f"le plus tard : {last_squats['date'].max().strftime('%H:%M:%S')}",
    delta_color="off",
)
st.caption("La personne qui en moyenne enregistre le premier et le dernier squat")

st.write("---")
fig = px.line(
    data_frame=filtered_df,
    x="date_day",
    y="squats",
    color="name",
    title="📈 Evolution des squats",
    line_shape="spline",
)
fig.update_layout(xaxis_title="Date", yaxis_title="Squats")
st.plotly_chart(fig, use_container_width=True)


# Plot stacked lines
fig = px.area(
    data_frame=daily_squats,
    x="date_day",
    y="cumulative_squats",
    line_group="name",
    color="name",
    title=" Squats CULmulés",
)
fig.update_layout(xaxis_title="Date", yaxis_title="Squats")
st.plotly_chart(fig, use_container_width=True)


# Scatter plot of squats over time colored by person
fig = px.scatter(
    data_frame=filtered_df,
    x="date_day",
    y="squats",
    color="name",
    title="Ce graph est cool non ?",
)
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Squats",
    shapes=[
        {
            "type": "line",
            "yref": "y",
            "y0": 40,
            "y1": 40,
            "xref": "paper",  # Use 'paper' for x-axis values between 0 and 1
            "x0": 0,
            "x1": 1,
            "line": {"color": "red", "width": 2},
        }
    ],
)
st.plotly_chart(fig, use_container_width=True)

consistent_squatter = filtered_df.groupby("name")["squats"].std().idxmin()
least_consistent_squatter = filtered_df.groupby("name")["squats"].std().idxmax()
average_squats_per_session = filtered_df.groupby("name")["squats"].mean()
total_sessions = filtered_df.groupby("name")["date_day"].nunique()


# Display additional metrics
st.write("---")

st.metric(
    label="🎲 Squatteur le plus régulier :",
    value=str(consistent_squatter),
    delta=df.groupby("name")["squats"].std().min(),
)
st.metric(
    label="🎲 Squatteur le plus random :",
    value=str(least_consistent_squatter),
    delta=df.groupby("name")["squats"].std().max(),
)

# Box plot of squats distribution across people
fig = px.box(
    data_frame=df, x="name", y="squats", title="📊 Distribution des squats par session"
)
fig.update_layout(
    xaxis_title="Qui ?",
    yaxis_title="Squats",
    shapes=[
        {
            "type": "line",
            "yref": "y",
            "y0": 40,
            "y1": 40,
            "xref": "paper",  # Use 'paper' for x-axis values between 0 and 1
            "x0": 0,
            "x1": 1,
            "line": {"color": "red", "width": 2},
        }
    ],
)
st.plotly_chart(fig, use_container_width=True)

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
st.write("---")
# Name with max sum of squats and sum of squats
person_max_sum = df.groupby("name")["squats"].sum().idxmax()
person_min_sum = df.groupby("name")["squats"].sum().idxmin()
sum_squats = df["squats"].sum()
st.metric(
    label="Qui a fait le plus de squats ?",
    value=person_max_sum,
    delta=f"{int(df.groupby('name')['squats'].sum().max())} gros squats",
)
st.metric(label="Somme des squats de l'équipe", value=int(sum_squats))
st.metric(
    label="Qui a fait le moins de squats ?",
    value=person_min_sum,
    delta=f"{int(df.groupby('name')['squats'].sum().min())} squats, lâche rien mon reuf",
    delta_color="inverse",
)

# Pie chart of proportion of squats done by each person
fig = px.pie(
    data_frame=df,
    names="name",
    values="squats",
    title="🍑 Proportion des squats par squatteur : ",
)
st.plotly_chart(fig, use_container_width=True)

# Bar chart of total squats done by each person
total_squats = df.groupby("name")["squats"].sum().reset_index()
# order the bars
total_squats = total_squats.sort_values(by="squats", ascending=False)
fig = px.bar(
    total_squats, x="name", y="squats", title="Somme des squats par participant"
)
fig.update_layout(
    # hide x label
    xaxis_title=None,
    yaxis_title="Squats",
)
st.plotly_chart(fig, use_container_width=True)
# $$$$$$$$$$$$$$$$$$$$$$$$$$
test = filtered_df.groupby("name")["squats"].mean().reset_index()
test = test.sort_values(by="squats", ascending=False)



st.write("---")
# Name with max sum of squats and sum of squats
person_max_mean = test.groupby("name")["squats"].mean().idxmax()
person_min_mean = test.groupby("name")["squats"].mean().idxmin()
mean_squats = test["squats"].mean()
st.metric(
    label="Qui a fait le plus de squats par jour en moyenne?",
    value=person_max_mean,
    delta=f"{int(test.groupby('name')['squats'].mean().max())} squats/jour",
)
st.metric(label="Moyenne des squats par jour de l'équipe", value=int(mean_squats))
st.metric(
    label="Qui a fait le moins de squats ?",
    value=person_min_mean,
    delta=f"{int(test.groupby('name')['squats'].mean().min())} squats/jour",
    delta_color="inverse")

st.caption("Le calcul de la moyenne est indépendant de l'objectif de chaque participant.")

fig = px.bar(
    test, x="name", y="squats", title="Moyenne des squats par participant et par jour"
)
fig.update_layout(
        shapes=[
        {
            "type": "line",
            "yref": "y",
            "y0": 40,
            "y1": 40,
            "xref": "paper",  # Use 'paper' for x-axis values between 0 and 1
            "x0": 0,
            "x1": 1,
            "line": {"color": "red", "width": 2},
        }
    ],
    xaxis_title=None,
    yaxis_title="Moyenne Squats",

)
st.plotly_chart(fig, use_container_width=True)








# Group by 'name' and count the number of sessions
sessions_count = daily_squats.groupby("name").size()

# Select names with more than 10 sessions
names_with_more_than_10_sessions = sessions_count[sessions_count > 5].index.tolist()

# Filter daily_squats DataFrame for names with more than 10 sessions
filtered_daily_squats = daily_squats[
    daily_squats["name"].isin(names_with_more_than_10_sessions)
]


pivot_df = filtered_daily_squats.pivot_table(
    index="date_day", columns="name", values="squats", aggfunc="sum"
)
# pivot_df
# Calculate the correlation matrix
correlation_matrix = pivot_df.corr()

# Plot heatmap
# Plot heatmap using Plotly Express
fig = px.imshow(
    correlation_matrix,
    labels=dict(x="Names", y="Names", color="Correlation"),
    x=correlation_matrix.columns,
    y=correlation_matrix.columns,
    color_continuous_scale="Viridis",
)

fig.update_layout(
    title="🫂 Correlation entre squatteurs", xaxis_title=None, yaxis_title=None
)


# Display the plot
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Qui squat avec qui ? Minimum 5 jours de squats pour calculer les corrélations."
)


# df['hour'] = df['date'].dt.hour


# df = df[df['name'].isin(names_with_more_than_10_sessions)]

# pivot_df = df.pivot_table(index='date_day', columns='name', values='hour', aggfunc='median')


# # Calculate the correlation matrix
# correlation_matrix = pivot_df.corr()

# # Plot heatmap
# # Plot heatmap using Plotly Express
# fig = px.imshow(correlation_matrix,
#                 labels=dict(x="Names", y="Names", color="Correlation"),
#                 x=correlation_matrix.columns,
#                 y=correlation_matrix.columns,
#                 color_continuous_scale="Viridis")

# fig.update_layout(title="🫂 Correlation de l'heure du squat",
#                   xaxis_title=None,
#                   yaxis_title=None
#                   )


# # Display the plot
# st.plotly_chart(fig, use_container_width=True)
# st.caption("Qui squat en meme temps que qui ? Minimum 5 jours de squats pour calculer les corrélations.")
