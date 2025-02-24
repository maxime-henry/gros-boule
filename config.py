import boto3
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from boto3.dynamodb.conditions import Attr
import pandas as pd
import asyncio

load_dotenv()

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")

today = datetime.now()+timedelta(hours=1)
# today = datetime(2025,2,20)

end_of_year = datetime(today.year, 12, 31)




def save_new_squat(name, squats_count):
    new_item = {
        "name": name,
        "date": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "squats": squats_count,
    }
    table_squats.put_item(Item=new_item)
    return new_item


class Participant:
    def __init__(self, name, df, days_left, squat_objectif_quotidien = 20 ):
        """
        Initialise un participant avec ses statistiques.
        :param name: Nom du participant
        :param df: DataFrame contenant les données ('name', 'squats', 'date')
        :param squat_objectif: Objectif de squats à atteindre
        """
        self.name = name
        self.squat_objectif_quotidien = squat_objectif_quotidien

        # Filtrer les données du participant
        self.df = df[df["name"] == name].copy()
        self.df["date"] = pd.to_datetime(self.df["date"]).dt.date  # Garder seulement la date

        # Calculs des statistiques
        self.sum_squats_done = self.df["squats"].sum()
        # sum squats aujourdhui 
        self.sum_squats_done_today = self.df[self.df["date"] == today.date()]["squats"].sum()
        self.premier_squat_date = self.df["date"].min() if not self.df.empty else datetime.now().date()
        self.squats_restants = days_left* squat_objectif_quotidien
    

        self.objectif_sum_squat = self._objectif_sum_squat()
        self.nombre_jours_depuis_debut = self._nombre_jours_depuis_debut()
        self.sum_squat_should_be_done_today = self.nombre_jours_depuis_debut * squat_objectif_quotidien
        self.delta_done_vs_objecitf_today = self.sum_squats_done - self.sum_squat_should_be_done_today
        self.moyenne_squats_par_jour = (self.sum_squats_done / self.nombre_jours_depuis_debut
            if self.nombre_jours_depuis_debut > 0 else 0)
        self.sum_squats_hier = self._yesterday_squats()


    def _objectif_sum_squat(self):
        if not self.premier_squat_date:
            return self.squats_restants  # Sécurité si premier squat inconnu

        total_day_challenge = (end_of_year.date() - self.premier_squat_date).days

        return total_day_challenge * self.squat_objectif_quotidien
    
    def _nombre_jours_depuis_debut(self):
        """ Calcule le nombre de jours actifs. """
        current_date = datetime.now() + timedelta(hours=1)
        return (current_date.date() - self.premier_squat_date).days + 1
    
    # calculer somme des squats d'hier 
    def _yesterday_squats(self):
        yesterday = datetime.now() + timedelta(hours=1) - timedelta(days=1)
        yesterday = yesterday.date()
        return self.df[self.df["date"] == yesterday]["squats"].sum()
    


    def __repr__(self):
        return (f"Participant(name={self.name}, sum_squats_done={self.sum_squats_done}, "
                f"premier_squat_date={self.premier_squat_date}, squats_restants={self.squats_restants}, "
                f"objectif_sum_squat={self.objectif_sum_squat}," 
                f"nombre_jours_depuis_debut={self.nombre_jours_depuis_debut},"
                f"sum_squat_should_be_done_today={self.sum_squat_should_be_done_today},"
                f"delta_done_vs_objecitf_today={self.delta_done_vs_objecitf_today},"
                f"moyenne_squats_par_jour={self.moyenne_squats_par_jour:.2f},"  
                f"somme_squats_hier={self.sum_squats_hier},"
                f"sum_squats_done_today={self.sum_squats_done_today},"
                )





# Assuming you have AWS credentials set up or using other methods to authenticate with DynamoDB
table_squats = boto3.resource(
    "dynamodb",
    region_name="eu-central-1",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY,
).Table(
    "squats"
)

# def load_data(name, data = None):

#     # Get the current year
#     if data is None:
        
#         current_year = datetime.now().year
#         result = table_squats.scan(FilterExpression=Attr("name").eq(name))
#         filtered_items = [
#         item for item in result["Items"]
        
#         if datetime.strptime(item["date"], "%Y-%m-%dT%H:%M:%S.%f").year == current_year
#     ]

#     else : 
#         filtered_items = data[data['name']==name]


# # Convert date strings to datetime objects and find the earliest date
#     try:
#         earliest_date = min(datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S.%f").date() for item in filtered_items)
#     except:
#         earliest_date = today.date()

#     total_day_challenge = (end_of_year.date() - earliest_date).days

#     total_squat_challenge = total_day_challenge * 20



#     squats_by_day = defaultdict(int)

#     for item in filtered_items:
#         date = item["date"][:10]  # Extract only the date part
#         squats_done = int(item["squats"])
#         squats_by_day[date] += squats_done

#     # Create a DataFrame
#     df = pd.DataFrame(list(squats_by_day.items()), columns=["Date", "Squats"])
#     done = df["Squats"].sum()

#     return Personne(name, done, df,earliest_date,total_squat_challenge)




def load_all():
    result = table_squats.scan()
    df = pd.DataFrame(result['Items'])
    df['date'] = pd.to_datetime(df['date'])

    # Filter rows for the current year
    current_year = datetime.now().year
    df = df[df['date'].dt.year == current_year]

    return df



def today_data(data = None, date = None):
    if data is None:
        data = load_all()
    data = data.copy()
    data['date'] = data['date'].dt.date

    target_date = date if date is not None else (datetime.now()+timedelta(hours=1)).date()

    extract = data[data["date"]==target_date].reset_index()
    # return only name and squats
    return extract[['name', 'squats']]
    


# print(data[data["date"].date()== today])

from mistralai import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-large-latest"

client = Mistral(api_key=api_key)


def mistral_chat(message):
    try : 
        chat_response = client.agents.complete(
            agent_id="ag:71fb9a73:20250208:untitled-agent:774ff24a",
            messages = [
                {
                    "role": "user",
                    "content": message,
                },
            ]
        )
        return chat_response.choices[0].message.content
    except :
        return "Bon courage mon reuf"

