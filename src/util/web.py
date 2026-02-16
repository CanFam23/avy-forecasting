from datetime import datetime
import json
import logging
import os
from typing import List, Tuple
from zoneinfo import ZoneInfo

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

from src.config import COORDS_SUBSET_FP
from src.util.model import get_elevation_band

logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_PROMPT = """Given the following data, produce a avalanche forecast for each zone. Produce the following for each zone:
1. The primary concern based on the given data.
2. A dicussion (In paragraph like format) dicussing each elevation band and slope aspect.
3. Travel advice, including what terrain to avoid (Aspects, slope, terrain type, etc.) and where the best snow will be.
The best snow is defined as the safest and highest quality. 

Keep in mind that the data is averaged over several observation points for each zone and elevation band, regardless of if 'avg' appears in the column name or not.

Also note that the data given are from simulations of the snowpack, so they are all estimated values.

Structure your response according to the given schema.
"""

GEMINI_SI = """You are an AI model named AvyAI. You're job is to produce daily avalanche forecasts for
mountain ranges around Whitefish, Montana, USA.

Rules / Guidelines:
Keep each forecast independent. They can mention similar topics, but should never mention other forecast zones.
Ignore anomalies in the data, such as when lower elevations get precipitation while upper elevations show none. **THIS IS VERY IMPORTANT**
Keep respones grounded in the given data.
Generate structured, technically precise avalanche forecasts.
Use meteorological terminology where appropriate.
Do not include conversational language.
"""

MT_TZ = ZoneInfo('America/Denver')

class Forecast(BaseModel):
    zone: str = Field(description="The name of the forecast zone.")
    primary_concern: str = Field(
        description="The primary avalanche concern(s) for the given zone and day")
    discussion: str = Field(
        description="A paragraph-like discussion about weather, including elevation band and slope aspect")
    travel_advice: str = Field(
        description="Advice on traveling through the zone for the current day.")


class AvalancheForecast(BaseModel):
    date: str = Field(
        description="Date the forecasts are valid for (MM-DD-YYYY)")
    forecasts: List[Forecast]


def gen_ai_forecast(
    actual_dangers_fp: str,
    all_dangers_fp: str,
    day_dangers_fp: str,
    weather_output_fp: str,
    forecast_output_fp: str,
) -> None:
    """
    Generate an avalanche forecast using daily weather features and Gemini.

    Args:
        actual_dangers_fp: Path to CSV of observed avalanche danger.
        all_dangers_fp: Path to CSV of weather/snowpack features.
        day_dangers_fp: Path to CSV of predicted danger values.
        weather_output_fp: Output path for generated daily weather JSON.
        forecast_output_fp: Output path for generated forecast JSON.
    """
    today = pd.Timestamp.now(tz=MT_TZ).normalize()


    daily = get_daily_weather(
        today,
        actual_dangers_fp,
        all_dangers_fp,
        day_dangers_fp,
        weather_output_fp,
    )

    if os.path.exists(forecast_output_fp):
        with open(forecast_output_fp, "r") as f:
            current_data = json.load(f)
            if current_data.get("date") and current_data.get("date") == today.strftime("%m-%d-%Y"):
                logger.info(f"{forecast_output_fp} already contains forecast for {datetime.now().date()}")
                return
            
    logger.info(f"Generating AI forecast for {today}")
    
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=(
            f"{GEMINI_PROMPT}\n"
            f"date: {today.strftime('%m-%d-%Y')}\n"
            f"data:\n{daily.to_markdown(index=False)}"
        ),
        config={
            "response_mime_type": "application/json",
            "response_json_schema": AvalancheForecast.model_json_schema(),
            "system_instruction": GEMINI_SI,
        },
    )

    # Get formatted JSON response
    forecast = AvalancheForecast.model_validate_json(
        response.text)  # type: ignore

    with open(forecast_output_fp, "w") as f:
        json.dump(forecast.model_dump(), f, indent=2)

def get_daily_weather(
    date: pd.Timestamp,
    actual_dangers_fp: str,
    all_dangers_fp: str,
    day_dangers_fp: str,
    output_fp: str,
) -> pd.DataFrame:
    """
    Build aggregated daily weather features for given date's forecast.

    Reads input CSVs, merges weather + predicted danger data,
    filters to given date (Mountain Time), aggregates features,
    performs unit conversions, writes JSON output, and returns results.

    Args:
        date: Date to get weather for
        actual_dangers_fp: Path to CSV containing observed avalanche danger.
        all_dangers_fp: Path to CSV containing weather/snowpack features.
        day_dangers_fp: Path to CSV containing predicted danger values.
        output_fp: Path to write daily weather JSON payload.

    Returns:
        Tuple containing:
            - pd.DataFrame: Aggregated daily features (with date_epoch).
            - pd.Timestamp: Normalized MT timestamp used for filtering.
    """

    if os.path.exists(output_fp):
        with open(output_fp, "r") as f:
            current_data = json.load(f)
            if current_data.get("date") and current_data.get("date") == int(date.timestamp()):
                logger.info(f"{output_fp} already contains data for {date}")
                return pd.DataFrame(current_data["weather"])
            
    logger.info(f"Aggregating data for {date}")

    actual_dangers = pd.read_csv(actual_dangers_fp)
    actual_dangers['date'] = pd.to_datetime(
        actual_dangers['date']).dt.tz_localize(MT_TZ)

    all_danger = pd.read_csv(all_dangers_fp)
    all_danger = all_danger[all_danger['slope_angle'] == 38.0]
    all_danger['date'] = pd.to_datetime(
        all_danger['date']).dt.tz_localize(MT_TZ)

    # Need day data to get days predictions
    day_preds = pd.read_csv(day_dangers_fp)
    day_preds = day_preds[day_preds['slope_angle'] == "slope"]
    day_preds['date'] = pd.to_datetime(day_preds['date']).dt.tz_localize(MT_TZ)

    fac_coords = gpd.read_file(COORDS_SUBSET_FP).rename(
        columns={'lat': 'latitude', 'lon': 'longitude'})

    # Merge to get zone data
    combined_df = pd.merge(all_danger, fac_coords, on=['id'], how='inner').drop(
        columns=["latitude", "longitude", "geometry"])
    combined_df['elevation_band'] = combined_df['altitude'].apply(
        get_elevation_band)
    
    # Merge to get predicted danger
    combined_df = combined_df.merge(day_preds,
                                    on=["date", "zone_name", "elevation_band"]).drop(
                                        columns=["predicted_danger_x",
                                                 "slope_angle_y"]
    ).rename(columns={"predicted_danger_y": "predicted_danger", "slope_angle_x": "slope_angle"})

    combined_df = combined_df[combined_df["date"] == date]

    # Aggregate point data and get averages
    daily = (
        combined_df
        .groupby([
            'date',
            'zone_name',
            'elevation_band',
            'slope_angle',
            'slope_azi'
        ])
        .agg(
            # core weather
            temp_avg=('TA', 'mean'),
            rh_avg=('RH', 'mean'),

            wind_avg=('VW', 'mean'),
            wind_transport24=('wind_trans24', 'mean'),

            # precip
            new_snow_24=('HN24', 'mean'),
            new_snow_12=('HN12', 'mean'),
            new_snow_72_24=('HN72_24', 'mean'),
            precip_total=('PSUM24', 'mean'),

            # snowpack state / wetness / structure 
            snow_depth_avg=('HS_mod', 'mean'),
            swe_avg=('SWE', 'mean'),
            ski_pen_avg=('ski_pen', 'mean'),
            hoar_size_max=('hoar_size', 'max'),
            cold_content=('ColdContentSnow', 'mean'),
            liquid_water=('MS_Water', 'mean'),
            rain_mass=('MS_Rain', 'mean'),

            # solar / energy
            solar_in=('ISWR', 'sum'),

            danger_level=('predicted_danger', 'max')
        )
        .reset_index()
    )

    # Temperature (C to F)
    for c in ['temp_avg']:
        daily[c] = daily[c] * 9/5 + 32

    # Wind (m/s to mph)
    for c in ['wind_avg']:
        daily[c] = daily[c] * 2.23694

    # Snowfall / precip / depth (cm to inches)
    for c in ['new_snow_24', 'new_snow_12', 'new_snow_72_24', 'precip_total', 'snow_depth_avg', 'ski_pen_avg']:
        daily[c] = daily[c] * 0.393701

    # SWE (mm water equiv to inches water equiv)
    daily['swe_avg'] = daily['swe_avg'] / 25.4

    # Round for UI
    daily = daily.round({
        'temp_avg': 1, 'temp_min': 1, 'temp_max': 1,
        'rh_avg': 0,
        'wind_avg': 1, 'wind_max': 1, 'wind_drift_max': 1,
        'wind_transport24': 2,
        'new_snow_24': 1, 'new_snow_12': 1, 'new_snow_72_24': 1,
        'precip_total': 2,
        'snow_depth_avg': 1,
        'swe_avg': 2,
        'ski_pen_avg': 1,
        'hoar_size_max': 2,
        'cold_content': 0,
        'liquid_water': 2,
        'rain_mass': 2,
        'solar_in': 0
    }).sort_values(by=['date', 'zone_name', 'elevation_band'])

    # Convert times to epoch so they can be serialized by JSON
    daily["date_epoch"] = daily["date"].apply(lambda x: int(x.timestamp()))
    daily = daily.drop(columns=["date"])

    weather_data = {
        "date": int(daily['date_epoch'][0]),
        "weather": daily.to_dict(orient="records")
    }

    with open(output_fp, "w") as f:
        json.dump(weather_data, f, indent=2)

    return daily


if __name__ == "__main__":
    actual = "data/2526_FAC/FAC_danger_levels_25_cleaned.csv"
    all_dangers = "data/ops25_26/all_predictions.csv"
    day_dangers = "data/ops25_26/day_predictions.csv"

    print(gen_ai_forecast(actual, all_dangers, day_dangers,
          "web/avyAI/public/data/weather.json", "web/avyAI/public/data/forecast_discussion.json"))
