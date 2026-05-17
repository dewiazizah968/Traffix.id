"""
generate_hybrid.py
------------------
Traffix.id — Hybrid Traffic Dataset Generator (v3)

Generate a hybrid traffic dataset using:
- real YOLO traffic calibration
- urban traffic flow simulation
- dynamic weather conditions
- traffic incidents and events
- adaptive signal timing
Builds a 7-day, 40,320-row time-series dataset (hybrid_traffic_7d.csv)

Usage:
    python generate_hybrid.py
    python generate_hybrid.py --input traffic_features.csv --output hybrid_traffic_7d.csv

Output:
    hybrid_traffic_7d.csv  — 7 days, 40,320 rows (10,080 ticks x 4 approaches)
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import random
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
INTERSECTION_ID = "JKT-TMG-SIM-01"
LOCATION_NAME   = "Koridor Tomang - Jakarta (Simulated)"
WIB        = ZoneInfo("Asia/Jakarta")
APPROACHES = ["N", "E", "S", "W"]

# YOLO approach -> output approach mapping
YOLO_MAP = {
    "LEFT":   "W",
    "CENTER": "N",
    "RIGHT":  "E",
    # "S" is synthetically generated from overall YOLO distribution
}

# Simulation time
START_DATE    = datetime(2026, 5, 1, 0, 0, 0, tzinfo=WIB)
TOTAL_DAYS    = 7
TOTAL_TICKS   = TOTAL_DAYS * 24 * 60   # 10,080 ticks
EXPECTED_ROWS = TOTAL_TICKS * 4  # 40,320 rows

DEFAULT_SEED = 42

# Traffic signal
CYCLE_SECONDS   = 90
MIN_GREEN       = 20
MAX_GREEN       = 42   # consistent with dummy dataset (max observed ~42s)
FREE_FLOW_SPEED = 60.0
SAT_FLOW_VPH    = 1900  # vehicles per hour per lane at saturation

# Lanes per approach (affects capacity and density scaling)
LANES = {"N": 3, "E": 2, "S": 3, "W": 2}

# Peak hour windows: (hour_frac start, hour_frac peak, hour_frac end)
MORNING_PEAK = (6.0, 7.5, 9.0)
EVENING_PEAK = (16.0, 17.5, 19.0)

# Weekend demand reduction factor
WEEKEND_FACTOR = 0.65

# Off-peak demand floor as fraction of peak — keeps traffic non-zero overnight
OFF_PEAK_FACTOR = 0.32

# Gaussian noise fraction applied to mean demand
FLOW_NOISE  = 0.15
SPEED_STD   = 1.2
DENSITY_STD = 0.5

# Label horizons in ticks (1 tick = 1 minute)
TARGET_15M = 15
TARGET_2H  = 120
TARGET_4H  = 240

# ---- Incident probabilities (per tick) ----
ACCIDENT_PROB     = 0.0003
ACCIDENT_DURATION = 30

ROADWORK_PROB     = 0.0002
ROADWORK_DURATION = 120

EVENT_PROB              = 0.0004
EVENT_DURATION          = 90
EVENT_DEMAND_MULTIPLIER = 1.3

# ---- Weather system ----
WEATHER_TYPES        = ["Clear", "Cloudy", "Hot", "Rain"]
WEATHER_PROBS        = [0.35, 0.30, 0.20, 0.15]
WEATHER_MIN_DURATION = 30  # minimum ticks before a weather change can occur

WEATHER_TEMP_RANGE = {
    "Clear":  (28.0, 33.0),
    "Cloudy": (26.0, 31.0),
    "Hot":    (32.0, 36.0),
    "Rain":   (23.0, 29.0),
}

# Speed reduction by weather condition (km/h subtracted from free-flow)
WEATHER_SPEED_REDUCTION = {
    "Clear":  0.0,
    "Cloudy": 2.0,
    "Hot":    0.0,
    "Rain":   9.0,
}

# Demand multiplier by weather
WEATHER_DEMAND_MULTIPLIER = {
    "Clear":  1.0,
    "Cloudy": 0.95,
    "Hot":    1.05,   # slight demand increase during heat
    "Rain":   0.85,
}

# Density boost factor by weather (rain -> slower clearance -> higher density)
WEATHER_DENSITY_MULTIPLIER = {
    "Clear":  1.0,
    "Cloudy": 1.0,
    "Hot":    1.0,
    "Rain":   1.25,
}

# ---- Peak demand targets per approach (veh/min at full peak) ----
# Calibrated to produce volume consistent with dummy_traffic_7d.csv:
#   N/S peak mean ~14 veh/min -> target 28-34 for realistic peak,
#   E/W peak mean ~7 veh/min  -> target 16-20.
PEAK_DEMAND = {
    "N": 31.0,
    "S": 28.0,
    "E": 18.0,
    "W": 16.0,
}

# Minimum demand floor (veh/min) — prevents runs of zero values at night
MIN_DEMAND = {
    "N": 3.5,
    "S": 3.0,
    "E": 1.5,
    "W": 1.5,
}

DEFAULT_SEED = 42

# ---------------------------------------------------------------------------
# LOAD YOLO CALIBRATION
# ---------------------------------------------------------------------------
def load_calibration_data(csv_path: str) -> dict:
    """
    Load traffic_features.csv and extract per-approach calibration stats.

    YOLO data is used for:
      - speed baseline per approach (yolo_mean_speed)
      - variability shape (coefficient of variation for noise scaling)
      - density and queue character

    Volume magnitude is governed separately by PEAK_DEMAND_TARGETS,
    allowing the hybrid dataset to reach realistic urban peak volumes
    while remaining grounded in the YOLO distribution shape.
    """
    df = pd.read_csv(csv_path)
    calibration = {}
    
    for yolo_ap, sim_ap in YOLO_MAP.items():
        sub = df[df["approach"] == yolo_ap]
        if sub.empty:
            sub = df

        calibration[sim_ap] = {
            "mean_count": sub["vehicle_count_1min"].mean(),
            "std_count": sub["vehicle_count_1min"].std(),
            "mean_speed": sub["avg_speed_kmh"].mean(),
            "std_speed": sub["avg_speed_kmh"].std(),
            "mean_density": sub["density_percent"].mean(),
            "mean_queue": sub["queue_length_veh"].mean(),
        }

    # Approach S: synthesized from global YOLO distribution
    calibration["S"] = {
        "mean_count": df["vehicle_count_1min"].mean(),
        "std_count": df["vehicle_count_1min"].std(),
        "mean_speed": df["avg_speed_kmh"].mean() * 0.95,
        "std_speed": df["avg_speed_kmh"].std(),
        "mean_density": df["density_percent"].mean() * 1.1,
        "mean_queue": df["queue_length_veh"].mean(),
    }

    for ap in APPROACHES:
        stats = calibration[ap]
        log.info(
            (
                "Calibration %s -> "
                "mean_count=%.2f | "
                "mean_speed=%.2f | "
                "mean_density=%.2f"
            ),
            ap,
            stats["mean_count"],
            stats["mean_speed"],
            stats["mean_density"],
        )

    return calibration

# ---------------------------------------------------------------------------
# DEMAND HELPER
# ---------------------------------------------------------------------------
def raised_cosine(x, start, peak, end):
    """Generate a smooth traffic peak curve using a raised cosine function."""
    if x <= start or x >= end:
        return 0.0
    if x <= peak:
        half = peak - start
        return 0.5 * (1 - math.cos(math.pi * (x - start) / half)) if half else 1.0
    half = end - peak
    return 0.5 * (1 + math.cos(math.pi * (x - peak) / half)) if half else 1.0


def calculate_time_factor(hour_value: float, is_weekend: bool):
    """
    Compute traffic demand factor based on time-of-day and weekend conditions.
    """
    morning = raised_cosine(hour_value, *MORNING_PEAK)
    evening = raised_cosine(hour_value, *EVENING_PEAK)
    midday = raised_cosine(hour_value, 10.5, 12.5, 14.5) * 0.55

    peak_factor = max(morning, evening, midday)
    result = OFF_PEAK_FACTOR + ((1.0 - OFF_PEAK_FACTOR) * peak_factor)

    if is_weekend:
        result *= WEEKEND_FACTOR

    return result

# ---------------------------------------------------------------------------
# WEATHER STATE
# ---------------------------------------------------------------------------
class WeatherState:
    """
    Simulates dynamic weather conditions with persistent state duration and
    gradual temperature variation.
    """
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.condition = rng.choices(WEATHER_TYPES, weights=WEATHER_PROBS, k=1)[0]
        self.remaining_ticks = rng.randint(WEATHER_MIN_DURATION, WEATHER_MIN_DURATION * 5)
        low, high = WEATHER_TEMP_RANGE[self.condition]
        self.temperature = rng.uniform(low, high)  

    def step(self):
        self.remaining_ticks -= 1
        if self.remaining_ticks <= 0:
            self.condition = self.rng.choices(WEATHER_TYPES, weights=WEATHER_PROBS, k=1)[0]
            self.remaining_ticks = self.rng.randint(WEATHER_MIN_DURATION, WEATHER_MIN_DURATION * 7)
            low, high = WEATHER_TEMP_RANGE[self.condition]
            self.temperature = self.rng.uniform(low, high)
        else:
            low, high = WEATHER_TEMP_RANGE[self.condition]
            self.temperature += self.rng.gauss(0, 0.12)
            self.temperature = max(low, min(high, self.temperature))

    @property
    def temp_c(self):
        return round(self.temperature, 1)

# ---------------------------------------------------------------------------
# INCIDENT TRACKER
# ---------------------------------------------------------------------------
class IncidentTracker:
    """
    Handles random traffic incidents such as accidents, roadwork, and city 
    events affecting road capacity.
    """
    def __init__(self, probability: float, duration: int, capacity_multiplier: float, rng: random.Random):
        self.probability = probability
        self.duration = duration
        self.capacity_multiplier = capacity_multiplier
        self.rng = rng
        self.remaining = 0

    def step(self):
        if self.remaining > 0:
            self.remaining -= 1
        elif self.rng.random() < self.probability:
            self.remaining = self.rng.randint(
                max(1, self.duration // 2),
                self.duration,
            )

    @property
    def active(self):
        return self.remaining > 0

    @property
    def multiplier(self):
        return self.capacity_multiplier if self.active else 1.0

# ---------------------------------------------------------------------------
# SIGNAL HELPER
# ---------------------------------------------------------------------------
def get_capacity_per_minute(approach: str):
    """Maximum vehicle departures per 1-min tick at full saturation."""
    return (SAT_FLOW_VPH * LANES[approach] / 60.0)


def calculate_green_time(demand: dict):
    """
    Allocate traffic signal green time proportionally to traffic demand.
    """
    total = sum(demand.values()) or 1.0
    green_time = {}

    for ap, value in demand.items():
        seconds = int(round(CYCLE_SECONDS * value / total))
        seconds = max(MIN_GREEN, seconds)
        seconds = min(MAX_GREEN, seconds)
        green_time[ap] = seconds
    return green_time

# ---------------------------------------------------------------------------
# TRAFFIC METRICS
# ---------------------------------------------------------------------------
def calculate_speed(density: float, weather: str, base_speed: float, rng: random.Random):
    """
    Estimate vehicle speed based on density, weather, and YOLO baseline.
    """
    speed = min(base_speed * 1.05, FREE_FLOW_SPEED)
    speed *= (1.0 - density / 100.0)
    speed -= WEATHER_SPEED_REDUCTION[weather]
    speed += rng.gauss(0, SPEED_STD)
    speed = max(10.0, min(FREE_FLOW_SPEED, speed))
    return round(speed, 2)


def calculate_wait_time(queue: float, speed: float, density: float):
    """
    Estimate vehicle waiting time based on queue length and traffic density.
    """
    discharge_rate = max(speed / 10.0, 0.1)
    wait_time = queue / discharge_rate
    penalty = 1.0 + ((density / 100.0) ** 1.5) * 2.0
    wait_time *= penalty
    return round(min(wait_time, 60.0), 3)

# ---------------------------------------------------------------------------
# TARGET BUILDER
# ---------------------------------------------------------------------------
def build_targets(df: pd.DataFrame):
    """
    Build future traffic volume targets for 15-minute, 2-hour, 
    and 4-hour horizons.
    """
    for ap in APPROACHES:
        mask = df["approach"] == ap

        volume = (
            df.loc[mask, "volume_veh_per_hour"]
            .reset_index(drop=True)
            .astype(float)
        )

        # Generate future forecasting targets
        target_15 = volume.shift(-TARGET_15M).ffill()
        target_2h = volume.shift(-TARGET_2H).ffill()
        target_4h = volume.shift(-TARGET_4H).ffill()

        df.loc[mask, "target_volume_15m"] = target_15.values
        df.loc[mask, "target_volume_2h"] = target_2h.values
        df.loc[mask, "target_volume_4h"] = target_4h.values

    target_cols = [
        "target_volume_15m",
        "target_volume_2h",
        "target_volume_4h",
    ]

    for col in target_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )
        df[col] = df[col].round(2)

# ---------------------------------------------------------------------------
# MAIN SIMULATION
# ---------------------------------------------------------------------------
def simulate_traffic(calibration: dict, seed: int = DEFAULT_SEED):
    """
    Run hybrid traffic simulation using YOLO-calibrated traffic behavior.
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    weather_state = WeatherState(rng)
    accident = IncidentTracker(ACCIDENT_PROB, ACCIDENT_DURATION, 0.5, rng)
    roadwork = IncidentTracker(ROADWORK_PROB, ROADWORK_DURATION, 0.7, rng)
    city_event = IncidentTracker(EVENT_PROB, EVENT_DURATION, 1.0, rng)

    queue_data = {ap: 0.0 for ap in APPROACHES}
    data_rows = []

    log.info("Running simulation for %d ticks...", TOTAL_TICKS)

    for tick in range(TOTAL_TICKS):
        current_time = START_DATE + timedelta(minutes=tick)
        hour_value = (current_time.hour + current_time.minute / 60.0)
        is_weekend = current_time.weekday() >= 5

        time_factor = calculate_time_factor(hour_value, is_weekend)

        weather_state.step()
        accident.step()
        roadwork.step()
        city_event.step()

        weather = weather_state.condition
        weather_flow = WEATHER_DEMAND_MULTIPLIER[weather]
        density_factor = WEATHER_DENSITY_MULTIPLIER[weather]
        capacity_factor = (accident.multiplier * roadwork.multiplier)
        event_factor = (EVENT_DEMAND_MULTIPLIER if city_event.active else 1.0)

        # Midday traffic increase during hot weather
        hot_boost = (1.12 if weather == "Hot" and 11.0 <= hour_value <= 15.0 else 1.0)

        # ------------------------------------------------------------
        # build traffic demand
        # ------------------------------------------------------------
        traffic_flow = {}
        for ap in APPROACHES:
            stats = calibration[ap]

            mean_flow = (PEAK_DEMAND[ap] * time_factor * weather_flow * event_factor * hot_boost)

            mean_flow = max(mean_flow, MIN_DEMAND[ap])

            # Traffic variability from YOLO calibration
            variation = (stats["std_count"] / max(stats["mean_count"], 0.1))

            # Dynamic noise scaling for realistic flow variation
            sigma = max(mean_flow * max(FLOW_NOISE, variation * 0.4), 0.5)

            arrivals = np_rng.normal(mean_flow, sigma)
            traffic_flow[ap] = max(0.0, arrivals)

        green_time = calculate_green_time(traffic_flow)

        # ------------------------------------------------------------
        # build metrics
        # ------------------------------------------------------------
        for ap in APPROACHES:
            arrivals = traffic_flow[ap]
            green = green_time[ap]

            # Effective capacity based on signal timing and incidents
            capacity = (get_capacity_per_minute(ap) * (green / CYCLE_SECONDS) * capacity_factor)

            # Queue persistence between simulation ticks
            queue_data[ap] += arrivals
            departures = min(queue_data[ap], capacity)
            queue_data[ap] -= departures
            queue = max(0.0, queue_data[ap])

            # Density estimation using queue-to-capacity ratio
            density = (queue / max(get_capacity_per_minute(ap) * 2.0, 1.0)) * 100.0
            density *= density_factor
            density += np_rng.normal(0, DENSITY_STD)
            density = round(max(0.0, min(100.0, density)), 2)

            stats = calibration[ap]

            speed = calculate_speed(density, weather, stats["mean_speed"], rng)
            wait_time = calculate_wait_time(queue, speed, density)
            
            row = {
                "timestamp_wib": current_time.isoformat(),
                "tick": tick,
                "intersectionId": INTERSECTION_ID,
                "approach": ap,
                "vehicle_count_1min": int(round(arrivals)),
                "volume_veh_per_hour": round(arrivals * 60.0, 2),
                "avg_speed_kmh": speed,
                "queue_length_veh": int(math.ceil(queue)),
                "wait_time_min": wait_time,
                "green_seconds": green,
                "density_percent": density,
                "weather_condition": weather,
                "weather_temp_c": weather_state.temp_c,
                "accident_count": int(accident.active),
                "roadwork_flag": int(roadwork.active),
                "event_flag": int(city_event.active),
                "target_volume_15m": None,
                "target_volume_2h": None,
                "target_volume_4h": None,
            }

            data_rows.append(row)

        # Progress log every day
        if (tick + 1) % 1440 == 0:
            day = (tick + 1) // 1440
            log.info(
                    "Day %d/%d complete (%d rows generated)",
                    day,
                    TOTAL_DAYS,
                    len(data_rows),
                )

    df = pd.DataFrame(data_rows)
    build_targets(df)
    return df

# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------
def validate_dataset(df: pd.DataFrame):
    """
    Validate generated dataset quality before model training.
    """
    checks = [
        ("row count",
         len(df) == EXPECTED_ROWS),

        ("no negative queue",
         (df["queue_length_veh"] >= 0).all()),

        ("density valid",
         df["density_percent"].between(0, 100).all()),

        ("speed <= free flow",
            (df["avg_speed_kmh"] <= FREE_FLOW_SPEED).all()),

        ("4 approaches",
         df["approach"].nunique() == 4),

        ("target 15m valid",
         df["target_volume_15m"].notna().all()),

        ("target 2h valid",
         df["target_volume_2h"].notna().all()),

        ("target 4h valid",
         df["target_volume_4h"].notna().all()),

        ("weather valid",
         df["weather_condition"].isin(WEATHER_TYPES).all()),

        ("timestamp valid",
         df["timestamp_wib"].notna().all()),

        ("intersection consistent",
         (df["intersectionId"] == INTERSECTION_ID).all()),

        ("no negative vehicle count",
         (df["vehicle_count_1min"] >= 0).all()),

        ("N peak > 800 vph",
         (
             df[df["approach"] == "N"]
             ["volume_veh_per_hour"]
             .max() > 800
         )),

        ("S peak > 800 vph",
         (
             df[df["approach"] == "S"]
             ["volume_veh_per_hour"]
             .max() > 800
         )),
    ]

    log.info("Validation results:")

    for label, result in checks:
        status = "PASS" if result else "FAIL"
        log.info("[%s] %s", status, label)

# ---------------------------------------------------------------------------
# SUMMARY PRINTER
# ---------------------------------------------------------------------------
def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("HYBRID TRAFFIC DATASET SUMMARY  —  Traffix.id")
    print("=" * 65)
    print(f"Rows         : {len(df):,}")
    print(f"Intersection : {INTERSECTION_ID}")
    print(f"Location     : {LOCATION_NAME}")
    print(f"Approaches   : {sorted(df['approach'].unique().tolist())}")
    print(f"Time range   : {df['timestamp_wib'].iloc[0]}")
    print(f"           ->  {df['timestamp_wib'].iloc[-1]}")

    print("\n[Weather distribution]")

    # Remove duplicated weather rows per timestamp
    weather_dist = (
        df
        .drop_duplicates(subset=["tick"])
        ["weather_condition"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
    )

    print(weather_dist)

    print("\nAverage Metrics:")

    avg_metrics = (
        df[
            [
                "vehicle_count_1min",
                "volume_veh_per_hour",
                "avg_speed_kmh",
                "density_percent",
                "queue_length_veh",
            ]
        ]
        .mean()
        .round(2)
    )

    print(avg_metrics)

    print("\nPeak Volume:")

    for ap in APPROACHES:
        peak = (
            df[df["approach"] == ap]
            ["volume_veh_per_hour"]
            .max()
        )

        print(f"{ap}: {peak:.2f} vph")

    print("\nIncident Summary:")

    print(
        "Accident rows :",
        (df["accident_count"] > 0).sum()
    )

    print(
        "Roadwork rows :",
        (df["roadwork_flag"] > 0).sum()
    )

    print(
        "Event rows    :",
        (df["event_flag"] > 0).sum()
    )

    print("=" * 60)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="yolo pipeline\\dataset\\traffic_features.csv",
        help="Path to YOLO traffic_features.csv (default: traffic_features.csv)",
    )
    parser.add_argument(
        "--output",
        default="data\\hybrid_traffic_7d.csv",
        help="Output CSV path (default: hybrid_traffic_7d.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )
    args = parser.parse_args()

    # Resolve input path (support running from any working directory)
    input_path = args.input
    if not os.path.exists(input_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alternative  = os.path.join(script_dir, args.input)
        if os.path.exists(alternative):
            input_path = alternative
        else:
            log.error("Input file not found.)
            sys.exit(1)

    log.info("Loading calibration data...")                  
    log.info("Input  : %s", input_path)
    log.info("Output : %s", args.output)
    log.info("Seed   : %d", args.seed)

    # Load YOLO calibration
    calibration = load_calibration_data(input_path)
            
    # Generate dataset
    dataset = simulate_traffic(calibration=calibration, seed=args.seed)

    # Validate
    validate_dataset(dataset)

    # Print summary
    print_summary(df)

    # Save
    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)
    dataset.to_csv(args.output, index=False)

    log.info("Dataset saved -> %s", args.output)
    log.info("Total rows: %d", len(dataset))
    log.info("Dataset ready for LSTM preprocessing.")


if __name__ == "__main__":
    main()
