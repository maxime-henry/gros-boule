import boto3
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")


def get_today():
    """Return current datetime in UTC+1. Call this instead of using a static 'today' variable."""
    return datetime.now() + timedelta(hours=1)


def get_end_of_year():
    """Return end of current year based on get_today()."""
    return datetime(get_today().year, 12, 31)


def save_new_squat(name, value, *, exercise: str = "SQUAT", unit: str | None = None):
    """
    Backward compatible save function.
    - existing callers: save_new_squat(name, squats) still works (defaults to SQUAT)
    - new usage: save_new_squat(name, seconds, exercise="PLANK", unit="seconds")
    """
    now = datetime.utcnow() + timedelta(hours=1)
    iso = now.isoformat()
    date_day = now.date().isoformat()

    exercise = (exercise or "SQUAT").upper()
    if unit is None:
        unit = "seconds" if exercise == "PLANK" else "reps"

    new_item = {
        "name": name,
        "date": iso,
        "exercise": exercise,
        "value": int(value),
        "unit": unit,
        "date_day": date_day,
        "year": int(now.year),
    }

    # Keep legacy "squats" attribute so existing charts/Participant logic keep working
    if exercise == "SQUAT":
        new_item["squats"] = int(value)
    else:
        # Keep squats present but 0 to simplify aggregation
        new_item["squats"] = 0

    table_squats.put_item(Item=new_item)
    return new_item


class Participant:
    def __init__(self, name, df, days_left, squat_objectif_quotidien=20):
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
        self.df["date"] = pd.to_datetime(
            self.df["date"]
        ).dt.date  # Garder seulement la date

        # Calculs des statistiques
        self.sum_squats_done = self.df["squats"].sum()
        # sum squats aujourdhui
        today = get_today()
        self.sum_squats_done_today = self.df[self.df["date"] == today.date()][
            "squats"
        ].sum()
        self.premier_squat_date = (
            self.df["date"].min() if not self.df.empty else datetime.now().date()
        )
        self.squats_restants = days_left * squat_objectif_quotidien

        self.objectif_sum_squat = self._objectif_sum_squat()
        self.nombre_jours_depuis_debut = self._nombre_jours_depuis_debut()
        self.sum_squat_should_be_done_today = (
            self.nombre_jours_depuis_debut * squat_objectif_quotidien
        )
        self.delta_done_vs_objecitf_today = (
            self.sum_squats_done - self.sum_squat_should_be_done_today
        )
        self.moyenne_squats_par_jour = (
            self.sum_squats_done / self.nombre_jours_depuis_debut
            if self.nombre_jours_depuis_debut > 0
            else 0
        )
        self.sum_squats_hier = self._yesterday_squats()
        self.sessions_logged = len(self.df)
        self.daily_totals = self._build_daily_totals()
        streaks = self._compute_streaks()
        self.current_objective_streak = streaks["current"]
        self.best_objective_streak = streaks["best"]
        (
            self.weekly_total,
            self.previous_week_total,
            self.weekly_delta,
        ) = self._weekly_totals()
        self.projected_year_total = self._projected_sum()
        self.progress_pct_vs_objectif = (
            (self.sum_squats_done / self.objectif_sum_squat) * 100
            if self.objectif_sum_squat
            else 0
        )
        self.last_activity_date = self.df["date"].max() if not self.df.empty else None
        self.is_active_today = self.sum_squats_done_today > 0

        # Plank stats (using plank_seconds column from load_all)
        self.sum_plank_seconds = (
            int(self.df["plank_seconds"].sum())
            if "plank_seconds" in self.df.columns
            else 0
        )
        self.sum_plank_seconds_today = (
            int(self.df[self.df["date"] == today.date()]["plank_seconds"].sum())
            if "plank_seconds" in self.df.columns
            else 0
        )
        self.best_plank_seconds = (
            int(self.df["plank_seconds"].max())
            if "plank_seconds" in self.df.columns and not self.df.empty
            else 0
        )

        # Plank streaks and advanced stats
        self.plank_daily_totals = self._build_plank_daily_totals()
        plank_streaks = self._compute_plank_streaks()
        self.current_plank_streak = plank_streaks["current"]
        self.best_plank_streak = plank_streaks["best"]
        self.plank_sessions_count = (
            int((self.df["plank_seconds"] > 0).sum())
            if "plank_seconds" in self.df.columns
            else 0
        )
        self.plank_days_active = (
            len(self.df[self.df["plank_seconds"] > 0]["date"].unique())
            if "plank_seconds" in self.df.columns
            else 0
        )
        self.moyenne_plank_par_session = (
            self.sum_plank_seconds / self.plank_sessions_count
            if self.plank_sessions_count > 0
            else 0
        )
        self.moyenne_plank_par_jour_actif = (
            self.sum_plank_seconds / self.plank_days_active
            if self.plank_days_active > 0
            else 0
        )

    def _objectif_sum_squat(self):
        if not self.premier_squat_date:
            return self.squats_restants  # Sécurité si premier squat inconnu

        total_day_challenge = (get_end_of_year().date() - self.premier_squat_date).days

        return total_day_challenge * self.squat_objectif_quotidien

    def _nombre_jours_depuis_debut(self):
        """Calcule le nombre de jours actifs."""
        current_date = datetime.now() + timedelta(hours=1)
        return (current_date.date() - self.premier_squat_date).days + 1

    # calculer somme des squats d'hier
    def _yesterday_squats(self):
        yesterday = datetime.now() + timedelta(hours=1) - timedelta(days=1)
        yesterday = yesterday.date()
        return self.df[self.df["date"] == yesterday]["squats"].sum()

    def _build_daily_totals(self):
        today = get_today()
        if self.df.empty:
            base = pd.DataFrame({"date": [today.date()], "squats": [0]})
        else:
            base = self.df.groupby("date", as_index=False)["squats"].sum()

        start = pd.Timestamp(self.premier_squat_date)
        stop = pd.Timestamp(today.date())
        date_range = pd.date_range(start, stop, freq="D")

        completed = (
            base.set_index("date")
            .reindex(date_range, fill_value=0)
            .rename_axis("date")
            .reset_index()
        )
        completed["date"] = completed["date"].dt.date
        return completed

    def _build_plank_daily_totals(self):
        """Build daily plank totals similar to squats."""
        today = get_today()
        if self.df.empty or "plank_seconds" not in self.df.columns:
            return pd.DataFrame({"date": [today.date()], "plank_seconds": [0]})

        base = self.df.groupby("date", as_index=False)["plank_seconds"].sum()

        # Find first plank date
        plank_dates = self.df[self.df["plank_seconds"] > 0]["date"]
        if plank_dates.empty:
            return pd.DataFrame({"date": [today.date()], "plank_seconds": [0]})

        first_plank_date = plank_dates.min()
        start = pd.Timestamp(first_plank_date)
        stop = pd.Timestamp(today.date())
        date_range = pd.date_range(start, stop, freq="D")

        completed = (
            base.set_index("date")
            .reindex(date_range, fill_value=0)
            .rename_axis("date")
            .reset_index()
        )
        completed["date"] = completed["date"].dt.date
        return completed

    def _compute_plank_streaks(self, min_seconds: int = 30):
        """Compute plank streaks. A day counts if >= min_seconds of planking done."""
        current = 0
        best = 0
        last_date = None
        last_goal_met = False
        today_date = get_today().date()

        for _, row in self.plank_daily_totals.iterrows():
            goal_met = row["plank_seconds"] >= min_seconds
            date_value = row["date"]
            is_today = date_value == today_date

            if goal_met:
                if last_date and last_goal_met and (date_value - last_date).days == 1:
                    current += 1
                else:
                    current = 1
            else:
                if not is_today:
                    current = 0

            best = max(best, current)
            last_goal_met = goal_met
            last_date = date_value

        return {"current": current, "best": best}

    def _compute_streaks(self):
        current = 0
        best = 0
        last_date = None
        last_goal_met = False
        today_date = get_today().date()

        for _, row in self.daily_totals.iterrows():
            goal_met = row["squats"] >= self.squat_objectif_quotidien
            date_value = row["date"]

            # Skip today when computing current streak - don't break streak until day ends
            is_today = date_value == today_date

            if goal_met:
                if last_date and last_goal_met and (date_value - last_date).days == 1:
                    current += 1
                else:
                    current = 1
            else:
                # Only reset streak if it's not today (give the whole day to complete goal)
                if not is_today:
                    current = 0

            best = max(best, current)
            last_goal_met = goal_met
            last_date = date_value

        return {"current": current, "best": best}

    def _weekly_totals(self):
        if self.daily_totals.empty:
            return 0, 0, 0

        today_date = get_today().date()
        this_week_start = today_date - timedelta(days=6)
        prev_week_start = this_week_start - timedelta(days=7)
        prev_week_end = this_week_start - timedelta(days=1)

        mask_this_week = (self.daily_totals["date"] >= this_week_start) & (
            self.daily_totals["date"] <= today_date
        )
        mask_prev_week = (self.daily_totals["date"] >= prev_week_start) & (
            self.daily_totals["date"] <= prev_week_end
        )

        this_week_total = int(self.daily_totals.loc[mask_this_week, "squats"].sum())
        prev_week_total = int(self.daily_totals.loc[mask_prev_week, "squats"].sum())

        return this_week_total, prev_week_total, this_week_total - prev_week_total

    def _projected_sum(self):
        total_days = (get_end_of_year().date() - self.premier_squat_date).days + 1
        if total_days <= 0:
            return 0
        return int(self.moyenne_squats_par_jour * total_days)

    def __repr__(self):
        return (
            f"Participant(name={self.name}, sum_squats_done={self.sum_squats_done}, "
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
).Table("squats")

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
    items = []
    scan_kwargs = {}

    while True:
        result = table_squats.scan(**scan_kwargs)
        items.extend(result.get("Items", []))
        last_evaluated_key = result.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    if not items:
        return pd.DataFrame(
            columns=[
                "name",
                "squats",
                "date",
                "exercise",
                "value",
                "unit",
                "date_day",
                "plank_seconds",
            ]
        )

    df = pd.DataFrame(items)
    if "date" not in df:
        df["date"] = pd.Timestamp(get_today())

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # ---- Backward-compatible defaults for new attributes ----
    # Ensure "squats" always exists for existing UI/stats
    df["squats"] = (
        pd.to_numeric(df.get("squats", 0), errors="coerce").fillna(0).astype(int)
    )

    # Legacy rows have no "exercise" attribute
    if "exercise" not in df.columns:
        df["exercise"] = "SQUAT"
    else:
        df["exercise"] = df["exercise"].fillna("SQUAT").astype(str).str.upper()

    # Legacy rows have "squats" but no "value"
    if "value" not in df.columns:
        df["value"] = df["squats"]
    else:
        df["value"] = (
            pd.to_numeric(df["value"], errors="coerce").fillna(df["squats"]).astype(int)
        )

    # Unit attribute
    if "unit" not in df.columns:
        df["unit"] = df["exercise"].map(
            lambda ex: "seconds" if ex == "PLANK" else "reps"
        )
    else:
        df["unit"] = df["unit"].fillna(
            df["exercise"].map(lambda ex: "seconds" if ex == "PLANK" else "reps")
        )

    # Convenience column for plank stats (won't affect existing pages)
    df["plank_seconds"] = 0
    mask_plank = df["exercise"] == "PLANK"
    df.loc[mask_plank, "plank_seconds"] = (
        pd.to_numeric(df.loc[mask_plank, "value"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # Ensure date_day exists (useful for grouping without timezone drift)
    if "date_day" not in df.columns:
        df["date_day"] = df["date"].dt.date.astype(str)

    current_year = get_today().year
    df = df[df["date"].dt.year == current_year]

    return df.sort_values("date").reset_index(drop=True)


def today_data(data=None, date=None):
    if data is None:
        data = load_all()
    data = data.copy()
    data["date"] = data["date"].dt.date

    target_date = (
        date if date is not None else (datetime.now() + timedelta(hours=1)).date()
    )

    extract = data[data["date"] == target_date].reset_index()
    # return only name and squats
    return extract[["name", "squats"]]


# print(data[data["date"].date()== today])

from mistralai import Mistral

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)


def mistral_chat(message):
    try:
        chat_response = client.agents.complete(
            agent_id="ag:71fb9a73:20250208:untitled-agent:774ff24a",
            messages=[
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Mistral API error: {e}")
        # print(e)
        return "Bon courage mon reuf"


# Centralized cached data fetch - shared across all pages
_squat_dataframe_cache = {"data": None, "timestamp": None}
_CACHE_TTL_SECONDS = 120


def fetch_squat_dataframe_cached():
    """Centralized cached fetch for all pages. TTL = 120s."""
    import time

    now = time.time()
    if (
        _squat_dataframe_cache["data"] is not None
        and _squat_dataframe_cache["timestamp"] is not None
        and (now - _squat_dataframe_cache["timestamp"]) < _CACHE_TTL_SECONDS
    ):
        return _squat_dataframe_cache["data"]

    df = load_all()
    _squat_dataframe_cache["data"] = df.sort_values("date")
    _squat_dataframe_cache["timestamp"] = now
    return _squat_dataframe_cache["data"]


def clear_squat_dataframe_cache():
    """Clear the cache after writes."""
    _squat_dataframe_cache["data"] = None
    _squat_dataframe_cache["timestamp"] = None
