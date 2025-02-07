import boto3
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from boto3.dynamodb.conditions import Attr
import pandas as pd


load_dotenv()

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")

today = datetime.now()+timedelta(hours=1)
end_of_year = datetime(today.year, 12, 31)


class Personne:
    def __init__(self, name, done, somme_squat,earliest_date,total_squat_challenge):
        self.name = name
        self.done = done
        self.table = somme_squat
        self.earliest_date =earliest_date
        self.total_squat_challenge = total_squat_challenge



# Assuming you have AWS credentials set up or using other methods to authenticate with DynamoDB
table_squats = boto3.resource(
    "dynamodb",
    region_name="eu-central-1",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY,
).Table(
    "squats"
)

def load_data(name):

    # Get the current year
    current_year = datetime.now().year

    result = table_squats.scan(FilterExpression=Attr("name").eq(name))
    # get the first day of squat

        # Filter items for the current year
    filtered_items = [
        item for item in result["Items"]
        if datetime.strptime(item["date"], "%Y-%m-%dT%H:%M:%S.%f").year == current_year
    ]


# Convert date strings to datetime objects and find the earliest date
    try:
        earliest_date = min(datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S.%f").date() for item in filtered_items)
    except:
        earliest_date = today.date()

    total_day_challenge = (end_of_year.date() - earliest_date).days

    total_squat_challenge = total_day_challenge * 20



    squats_by_day = defaultdict(int)
    for item in filtered_items:
        date = item["date"][:10]  # Extract only the date part
        squats_done = int(item["squats"])
        squats_by_day[date] += squats_done

    # Create a DataFrame
    df = pd.DataFrame(list(squats_by_day.items()), columns=["Date", "Squats"])
    done = df["Squats"].sum()

    return Personne(name, done, df,earliest_date,total_squat_challenge)


def load_all():
    result = table_squats.scan()
    df = pd.DataFrame(result['Items'])
    df['date'] = pd.to_datetime(df['date'])

    # Filter rows for the current year
    current_year = datetime.now().year
    df = df[df['date'].dt.year == current_year]

    return df



def today_data(data = None):
    if data is None:
        data = load_all()
    data = data.copy()
    data['date'] = data['date'].dt.date
    extract = data[data["date"]==(datetime.now()+timedelta(hours=1)).date()].reset_index()
    # return only name and squats
    return extract[['name', 'squats']]
    


# print(data[data["date"].date()== today])