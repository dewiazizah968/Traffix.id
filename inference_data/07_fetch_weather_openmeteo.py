from pathlib import Path
from datetime import datetime
import time
import requests
import pandas as pd

# =========================
# PATH SETUP (FIX)
# =========================
BASE_DIR = Path(__file__).resolve().parent
METADATA_DIR = BASE_DIR / "metadata"

INPUT_CSV = METADATA_DIR / "video_metadata_with_coordinates.csv"
OUTPUT_CSV = METADATA_DIR / "video_weather_data.csv"
REPORT_CSV = METADATA_DIR / "weather_api_report.csv"

# =========================
# OPEN METEO CONFIG
# =========================
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "cloud_cover",
    "wind_speed_10m",
    "weather_code"
]


# =========================
# CLEAN FUNCTION
# =========================
def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in ["nan", "none", "null"]:
        return ""
    return text


# =========================
# SAFE FLOAT PARSER (FIXED)
# =========================
def parse_float(value):
    text = clean_text(value)

    if not text:
        return None

    text = text.replace(",", ".")

    try:
        val = float(text)

        # FILTER KOORDINAT RUSAK (ANTI DATA CORRUPT)
        if abs(val) > 1000:
            return None

        return val

    except ValueError:
        return None


# =========================
# TIMESTAMP PARSER (FIXED)
# =========================
def parse_timestamp_wib(value):
    text = clean_text(value)

    if not text:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


# =========================
# ROUND TO HOUR (SAFE)
# =========================
def round_to_hour(dt):
    if dt.minute >= 30:
        dt = dt.replace(minute=0, second=0, microsecond=0)
        if dt.hour == 23:
            return dt.replace(hour=0)
        return dt.replace(hour=dt.hour + 1)

    return dt.replace(minute=0, second=0, microsecond=0)


# =========================
# API FETCH
# =========================
def fetch_weather_for_location_date(lat, lon, date_text):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_text,
        "end_date": date_text,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": "Asia/Jakarta"
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


# =========================
# EXTRACT WEATHER
# =========================
def extract_hourly_weather(api_json, target_hour_text):
    hourly = api_json.get("hourly", {})
    times = hourly.get("time", [])

    if not times or target_hour_text not in times:
        return None

    idx = times.index(target_hour_text)

    result = {"weather_hour": target_hour_text}

    for var in HOURLY_VARIABLES:
        values = hourly.get(var, [])
        result[var] = values[idx] if idx < len(values) else ""

    return result


# =========================
# MAIN PIPELINE
# =========================
def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    required_columns = ["video_file", "timestamp_wib", "lat", "lon"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    weather_rows = []
    report_rows = []
    api_cache = {}

    print(f"[INFO] Total video: {len(df)}")

    for _, row in df.iterrows():

        video_file = clean_text(row["video_file"])
        lat = parse_float(row["lat"])
        lon = parse_float(row["lon"])
        dt = parse_timestamp_wib(row["timestamp_wib"])

        base = row.to_dict()

        # =========================
        # VALIDATION STEP
        # =========================
        if lat is None or lon is None:
            base.update({
                "weather_status": "failed",
                "weather_error": "lat_lon_invalid"
            })
            weather_rows.append(base)
            continue

        if dt is None:
            base.update({
                "weather_status": "failed",
                "weather_error": "timestamp_invalid"
            })
            weather_rows.append(base)
            continue

        # =========================
        # TIME NORMALIZATION
        # =========================
        target_dt = round_to_hour(dt)

        date_text = target_dt.strftime("%Y-%m-%d")
        target_hour_text = target_dt.strftime("%Y-%m-%dT%H:00")

        cache_key = (round(lat, 5), round(lon, 5), date_text)

        try:
            if cache_key not in api_cache:
                print(f"[API] Fetch weather {video_file}")

                api_cache[cache_key] = fetch_weather_for_location_date(
                    lat, lon, date_text
                )

                time.sleep(0.5)

                report_rows.append({
                    "cache_key": str(cache_key),
                    "lat": lat,
                    "lon": lon,
                    "date": date_text,
                    "status": "success",
                    "error_message": ""
                })

            api_json = api_cache[cache_key]

            weather = extract_hourly_weather(api_json, target_hour_text)

            if weather is None:
                base.update({
                    "weather_status": "failed",
                    "weather_error": "hour_not_found",
                    "weather_hour": target_hour_text
                })
            else:
                base.update(weather)
                base.update({
                    "weather_status": "valid",
                    "weather_error": ""
                })

            weather_rows.append(base)

        except Exception as e:
            err = str(e)[:500]

            base.update({
                "weather_status": "failed",
                "weather_error": err,
                "weather_hour": target_hour_text
            })

            weather_rows.append(base)

            report_rows.append({
                "cache_key": str(cache_key),
                "lat": lat,
                "lon": lon,
                "date": date_text,
                "status": "failed",
                "error_message": err
            })

            print(f"[FAILED] {video_file}: {err}")

    # =========================
    # SAVE OUTPUT
    # =========================
    pd.DataFrame(weather_rows).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(report_rows).to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    print("\n[SUCCESS] Weather pipeline selesai")
    print(f"[OUTPUT] {OUTPUT_CSV}")
    print(f"[OUTPUT] {REPORT_CSV}")


if __name__ == "__main__":
    main()