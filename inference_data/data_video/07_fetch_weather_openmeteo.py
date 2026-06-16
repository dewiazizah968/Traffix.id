from pathlib import Path
from datetime import datetime
import time
import requests
import pandas as pd

BASE_DIR = Path(".")
METADATA_DIR = BASE_DIR / "metadata"

INPUT_CSV = METADATA_DIR / "video_metadata_with_coordinates.csv"
OUTPUT_CSV = METADATA_DIR / "video_weather_data.csv"
REPORT_CSV = METADATA_DIR / "weather_api_report.csv"

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


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in ["nan", "none", "null"]:
        return ""
    return text


def parse_float(value):
    text = clean_text(value)
    if not text:
        return None

    text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def parse_timestamp_wib(value):
    text = clean_text(value)

    if not text:
        return None

    # Format utama dari pipeline kamu: 2026-05-18 07:09:35
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def round_to_hour(dt):
    """
    Membulatkan timestamp ke jam terdekat.
    Contoh:
    07:09 -> 07:00
    07:35 -> 08:00
    """
    if dt.minute >= 30:
        dt = dt.replace(hour=dt.hour, minute=0, second=0, microsecond=0)
        dt = dt + pd.Timedelta(hours=1)
        return dt.to_pydatetime() if hasattr(dt, "to_pydatetime") else dt

    return dt.replace(minute=0, second=0, microsecond=0)


def fetch_weather_for_location_date(lat, lon, date_text):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_text,
        "end_date": date_text,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": "Asia/Jakarta"
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def extract_hourly_weather(api_json, target_hour_text):
    hourly = api_json.get("hourly", {})

    times = hourly.get("time", [])

    if not times:
        return None

    if target_hour_text not in times:
        return None

    idx = times.index(target_hour_text)

    result = {
        "weather_hour": target_hour_text
    }

    for var in HOURLY_VARIABLES:
        values = hourly.get(var, [])

        if idx < len(values):
            result[var] = values[idx]
        else:
            result[var] = ""

    return result


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {INPUT_CSV}. "
            "Jalankan dulu 06_join_video_with_coordinates.py"
        )

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    required_columns = [
        "video_file",
        "timestamp_wib",
        "lat",
        "lon"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di {INPUT_CSV}: {col}")

    weather_rows = []
    report_rows = []

    # Cache supaya API tidak dipanggil berulang untuk lokasi dan tanggal yang sama
    api_cache = {}

    print(f"[INFO] Total video yang akan diproses: {len(df)}")

    for index, row in df.iterrows():
        video_file = clean_text(row["video_file"])
        timestamp_wib = clean_text(row["timestamp_wib"])

        lat = parse_float(row["lat"])
        lon = parse_float(row["lon"])

        dt = parse_timestamp_wib(timestamp_wib)

        base_output = row.to_dict()

        if lat is None or lon is None:
            base_output.update({
                "weather_status": "failed",
                "weather_error": "lat_or_lon_invalid"
            })
            weather_rows.append(base_output)
            continue

        if dt is None:
            base_output.update({
                "weather_status": "failed",
                "weather_error": "timestamp_wib_invalid"
            })
            weather_rows.append(base_output)
            continue

        target_dt = round_to_hour(dt)

        date_text = target_dt.strftime("%Y-%m-%d")
        target_hour_text = target_dt.strftime("%Y-%m-%dT%H:00")

        # Cache key dibulatkan supaya request tidak berlebihan
        cache_key = (
            round(lat, 5),
            round(lon, 5),
            date_text
        )

        try:
            if cache_key not in api_cache:
                print(f"[API] Fetch weather: lat={lat}, lon={lon}, date={date_text}")

                api_json = fetch_weather_for_location_date(
                    lat=lat,
                    lon=lon,
                    date_text=date_text
                )

                api_cache[cache_key] = api_json

                report_rows.append({
                    "cache_key": str(cache_key),
                    "lat": lat,
                    "lon": lon,
                    "date": date_text,
                    "status": "success",
                    "error_message": ""
                })

                # jeda kecil agar tidak terlalu agresif
                time.sleep(0.5)

            api_json = api_cache[cache_key]

            weather_data = extract_hourly_weather(
                api_json=api_json,
                target_hour_text=target_hour_text
            )

            if weather_data is None:
                base_output.update({
                    "weather_status": "failed",
                    "weather_error": f"hour_not_found_{target_hour_text}",
                    "weather_hour": target_hour_text
                })
            else:
                base_output.update(weather_data)
                base_output.update({
                    "weather_status": "valid",
                    "weather_error": ""
                })

            weather_rows.append(base_output)

        except Exception as e:
            error_message = str(e)[:500]

            base_output.update({
                "weather_status": "failed",
                "weather_error": error_message,
                "weather_hour": target_hour_text
            })

            weather_rows.append(base_output)

            report_rows.append({
                "cache_key": str(cache_key),
                "lat": lat,
                "lon": lon,
                "date": date_text,
                "status": "failed",
                "error_message": error_message
            })

            print(f"[FAILED] {video_file}: {error_message}")

    output_df = pd.DataFrame(weather_rows)
    output_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    print("\n[SUCCESS] Pengambilan data cuaca selesai.")
    print(f"[OUTPUT] Data cuaca video : {OUTPUT_CSV}")
    print(f"[OUTPUT] Report API        : {REPORT_CSV}")

    print("\nRingkasan weather_status:")
    print(
        output_df["weather_status"]
        .value_counts()
        .rename_axis("weather_status")
        .reset_index(name="count")
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()