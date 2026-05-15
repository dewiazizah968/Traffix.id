"""
generate_hybrid.py
------------------
Traffix.id — Hybrid Traffic Dataset Generator (v2)

Builds a 7-day, 40,320-row time-series dataset (hybrid_traffic_7d.csv)
calibrated from real YOLO detection results (traffic_features.csv),
with traffic volume and weather distribution consistent with dummy_traffic_7d.csv.

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
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
INTERSECTION_ID = "JKT-TMG-SIM-01"
LOCATION_NAME   = "Koridor Tomang - Jakarta (Simulated)"

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------
WIB       = ZoneInfo("Asia/Jakarta")
APPROACHES = ["N", "E", "S", "W"]

# YOLO approach -> output approach mapping
APPROACH_MAP = {
    "LEFT":   "W",
    "CENTER": "N",
    "RIGHT":  "E",
    # "S" is synthetically generated from overall YOLO distribution
}

# Simulation time
START_DT      = datetime(2026, 5, 1, 0, 0, 0, tzinfo=WIB)
TICKS_7D      = 7 * 24 * 60   # 10,080 ticks
EXPECTED_ROWS = TICKS_7D * 4  # 40,320 rows

# Traffic signal
CYCLE_SECONDS = 90
MIN_GREEN     = 20
MAX_GREEN     = 42   # consistent with dummy dataset (max observed ~42s)
V_FREE_KMH    = 60.0
SAT_FLOW_VPH  = 1900  # vehicles per hour per lane at saturation

# Lanes per approach (affects capacity and density scaling)
LANES = {"N": 3, "E": 2, "S": 3, "W": 2}

# Peak hour windows: (hour_frac start, hour_frac peak, hour_frac end)
MORNING_PEAK = (6.0, 7.5, 9.0)
EVENING_PEAK = (16.0, 17.5, 19.0)

# Weekend demand reduction factor
WEEKEND_FACTOR = 0.65

# Off-peak demand floor as fraction of peak — keeps traffic non-zero overnight
OFF_PEAK_FRACTION = 0.32

# Gaussian noise fraction applied to mean demand
NOISE_FRACTION        = 0.15
SPEED_NOISE_STD_KMH   = 1.2
DENSITY_NOISE_STD_PCT = 0.5

# Label horizons in ticks (1 tick = 1 minute)
HORIZON_15M = 15
HORIZON_2H  = 120
HORIZON_4H  = 240

# ---- Incident probabilities (per tick) ----
ACCIDENT_PROB     = 0.0003
ACCIDENT_DURATION = 30
ACCIDENT_CAP_MULT = 0.5

ROADWORK_PROB     = 0.0002
ROADWORK_DURATION = 120
ROADWORK_CAP_MULT = 0.7

EVENT_PROB        = 0.0004
EVENT_DURATION    = 90
EVENT_DEMAND_MULT = 1.3

# ---- Weather system ----
# Conditions match dummy_traffic_7d.csv: Clear, Cloudy, Hot, Rain
WEATHER_CONDITIONS  = ["Clear", "Cloudy", "Hot", "Rain"]
WEATHER_PROBS       = [0.35, 0.30, 0.20, 0.15]
WEATHER_MIN_PERSIST = 30  # minimum ticks before a weather change can occur

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
WEATHER_DEMAND_MULT = {
    "Clear":  1.0,
    "Cloudy": 0.95,
    "Hot":    1.05,   # slight demand increase during heat
    "Rain":   0.85,
}

# Density boost factor by weather (rain -> slower clearance -> higher density)
WEATHER_DENSITY_BOOST = {
    "Clear":  1.0,
    "Cloudy": 1.0,
    "Hot":    1.0,
    "Rain":   1.25,
}

# ---- Peak demand targets per approach (veh/min at full peak) ----
# Calibrated to produce volume consistent with dummy_traffic_7d.csv:
#   N/S peak mean ~14 veh/min -> target 28-34 for realistic peak,
#   E/W peak mean ~7 veh/min  -> target 16-20.
PEAK_DEMAND_TARGETS = {
    "N": 31.0,
    "S": 28.0,
    "E": 18.0,
    "W": 16.0,
}

# Minimum demand floor (veh/min) — prevents runs of zero values at night
DEMAND_FLOOR = {
    "N": 3.5,
    "S": 3.0,
    "E": 1.5,
    "W": 1.5,
}

DEFAULT_SEED = 42


# ---------------------------------------------------------------------------
# YOLO calibration loader
# ---------------------------------------------------------------------------

def load_yolo_stats(csv_path: str) -> dict:
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
    log.info("Loaded YOLO data: %d rows, approaches=%s",
             len(df), df["approach"].unique().tolist())

    stats: dict[str, dict] = {}

    for yolo_ap, out_ap in APPROACH_MAP.items():
        sub = df[df["approach"] == yolo_ap]
        if sub.empty:
            log.warning("Approach '%s' not found in YOLO data, using global stats", yolo_ap)
            sub = df

        stats[out_ap] = {
            "yolo_mean_count":   sub["vehicle_count_1min"].mean(),
            "yolo_std_count":    sub["vehicle_count_1min"].std(),
            "yolo_mean_density": sub["density_percent"].mean(),
            "yolo_std_density":  sub["density_percent"].std(),
            "yolo_mean_speed":   sub["avg_speed_kmh"].mean(),
            "yolo_std_speed":    sub["avg_speed_kmh"].std(),
            "yolo_mean_queue":   sub["queue_length_veh"].mean(),
        }

    # Approach S: synthesized from global YOLO distribution
    stats["S"] = {
        "yolo_mean_count":   df["vehicle_count_1min"].mean(),
        "yolo_std_count":    df["vehicle_count_1min"].std(),
        "yolo_mean_density": df["density_percent"].mean() * 1.1,
        "yolo_std_density":  df["density_percent"].std(),
        "yolo_mean_speed":   df["avg_speed_kmh"].mean() * 0.95,
        "yolo_std_speed":    df["avg_speed_kmh"].std(),
        "yolo_mean_queue":   df["queue_length_veh"].mean(),
    }

    for ap in APPROACHES:
        s = stats[ap]
        log.info(
            "Approach %s YOLO calibration: mean_count=%.2f  mean_speed=%.1f  mean_density=%.2f",
            ap, s["yolo_mean_count"], s["yolo_mean_speed"], s["yolo_mean_density"],
        )

    return stats


# ---------------------------------------------------------------------------
# Demand shape helpers
# ---------------------------------------------------------------------------

def _raised_cos(x: float, x_start: float, x_peak: float, x_end: float) -> float:
    """Raised-cosine bell weight in 0..1 range."""
    if x <= x_start or x >= x_end:
        return 0.0
    if x <= x_peak:
        half = x_peak - x_start
        return 0.5 * (1 - math.cos(math.pi * (x - x_start) / half)) if half else 1.0
    else:
        half = x_end - x_peak
        return 0.5 * (1 + math.cos(math.pi * (x - x_peak) / half)) if half else 1.0


def time_of_day_factor(hour_frac: float, is_weekend: bool) -> float:
    """
    Return demand multiplier in [OFF_PEAK_FRACTION, 1.0].
    Adds a gentle midday shoulder to prevent near-zero midday traffic.
    """
    morning = _raised_cos(hour_frac, MORNING_PEAK[0], MORNING_PEAK[1], MORNING_PEAK[2])
    evening = _raised_cos(hour_frac, EVENING_PEAK[0], EVENING_PEAK[1], EVENING_PEAK[2])
    midday  = _raised_cos(hour_frac, 10.5, 12.5, 14.5) * 0.55  # mild midday shoulder

    peak_w = max(morning, evening, midday)
    base   = OFF_PEAK_FRACTION + (1.0 - OFF_PEAK_FRACTION) * peak_w

    if is_weekend:
        base *= WEEKEND_FACTOR

    return base


# ---------------------------------------------------------------------------
# Weather state machine
# ---------------------------------------------------------------------------

class WeatherState:
    """
    Markov weather model with minimum persistence per state.
    Conditions: Clear, Cloudy, Hot, Rain (consistent with dummy dataset).
    """

    def __init__(self, rng: random.Random):
        self._rng = rng
        self._condition: str = rng.choices(WEATHER_CONDITIONS, weights=WEATHER_PROBS, k=1)[0]
        self._ticks_left: int = rng.randint(WEATHER_MIN_PERSIST, WEATHER_MIN_PERSIST * 5)
        lo, hi = WEATHER_TEMP_RANGE[self._condition]
        self._temp_c: float = rng.uniform(lo, hi)

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def temp_c(self) -> float:
        return round(self._temp_c, 1)

    def step(self) -> None:
        self._ticks_left -= 1
        if self._ticks_left <= 0:
            self._condition  = self._rng.choices(WEATHER_CONDITIONS, weights=WEATHER_PROBS, k=1)[0]
            self._ticks_left = self._rng.randint(WEATHER_MIN_PERSIST, WEATHER_MIN_PERSIST * 7)
            lo, hi = WEATHER_TEMP_RANGE[self._condition]
            self._temp_c = self._rng.uniform(lo, hi)
        else:
            lo, hi = WEATHER_TEMP_RANGE[self._condition]
            noise  = self._rng.gauss(0, 0.12)
            self._temp_c = max(lo, min(hi, self._temp_c + noise))


# ---------------------------------------------------------------------------
# Incident tracker
# ---------------------------------------------------------------------------

class IncidentTracker:
    def __init__(self, prob: float, duration: int, cap_mult: float, rng: random.Random):
        self._prob      = prob
        self._duration  = duration
        self._cap_mult  = cap_mult
        self._rng       = rng
        self._remaining = 0

    @property
    def active(self) -> bool:
        return self._remaining > 0

    @property
    def capacity_multiplier(self) -> float:
        return self._cap_mult if self.active else 1.0

    def step(self) -> None:
        if self._remaining > 0:
            self._remaining -= 1
        elif self._rng.random() < self._prob:
            self._remaining = self._rng.randint(
                max(1, self._duration // 2), self._duration
            )


# ---------------------------------------------------------------------------
# Traffic signal helpers
# ---------------------------------------------------------------------------

def sat_flow_per_tick(approach: str) -> float:
    """Maximum vehicle departures per 1-min tick at full saturation."""
    return SAT_FLOW_VPH * LANES[approach] / 60.0


def alloc_green(demand: dict[str, float]) -> dict[str, int]:
    """Proportional green time allocation clamped to [MIN_GREEN, MAX_GREEN]."""
    total = sum(demand.values()) or 1.0
    return {
        ap: max(MIN_GREEN, min(MAX_GREEN, int(round(CYCLE_SECONDS * d / total))))
        for ap, d in demand.items()
    }


# ---------------------------------------------------------------------------
# Speed model
# ---------------------------------------------------------------------------

def compute_speed(
    density_pct: float,
    weather: str,
    yolo_mean_speed: float,
    rng: random.Random,
) -> float:
    """
    Greenshields-based speed with YOLO-calibrated free-flow anchor.
    At zero density: approaches min(yolo_mean_speed * 1.05, 60) km/h.
    Rain and high density reduce speed toward 10 km/h minimum.
    """
    free_speed = min(yolo_mean_speed * 1.05, V_FREE_KMH)
    v  = free_speed * (1.0 - density_pct / 100.0)
    v -= WEATHER_SPEED_REDUCTION.get(weather, 0.0)
    v += rng.gauss(0, SPEED_NOISE_STD_KMH)
    return round(max(10.0, min(V_FREE_KMH, v)), 2)


# ---------------------------------------------------------------------------
# Wait time model
# ---------------------------------------------------------------------------

def compute_wait_time(queue: float, speed: float, density_pct: float) -> float:
    """
    Wait time (minutes) based on queue length, speed, and density.
    Non-linear increase at high density (> 50%).
    """
    departure_rate = max(speed / 10.0, 0.1)
    base_wait      = queue / departure_rate
    density_factor = 1.0 + (density_pct / 100.0) ** 1.5 * 2.0
    return round(min(base_wait * density_factor, 60.0), 3)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate(
    yolo_stats: dict,
    total_ticks: int = TICKS_7D,
    seed: int = DEFAULT_SEED,
    start_dt: datetime = START_DT,
) -> pd.DataFrame:
    """
    Generate the hybrid traffic dataset.

    Parameters
    ----------
    yolo_stats   : calibration dict from load_yolo_stats()
    total_ticks  : number of 1-minute ticks (default 10,080 = 7 days)
    seed         : RNG seed for reproducibility
    start_dt     : simulation start datetime (WIB-aware)

    Returns
    -------
    pd.DataFrame  with EXPECTED_ROWS rows (total_ticks x 4 approaches)
    """
    rng    = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # Shared intersection-level state
    weather  = WeatherState(rng)
    accident = IncidentTracker(ACCIDENT_PROB, ACCIDENT_DURATION, ACCIDENT_CAP_MULT, rng)
    roadwork = IncidentTracker(ROADWORK_PROB, ROADWORK_DURATION, ROADWORK_CAP_MULT, rng)
    event    = IncidentTracker(EVENT_PROB, EVENT_DURATION, 1.0, rng)

    # Per-approach vehicle queue (vehicles)
    queues: dict[str, float] = {ap: 0.0 for ap in APPROACHES}

    rows: list[dict] = []

    log.info("Simulating %d ticks (%d rows expected)...", total_ticks, total_ticks * 4)

    for tick in range(total_ticks):
        dt         = start_dt + timedelta(minutes=tick)
        hour_frac  = dt.hour + dt.minute / 60.0
        is_weekend = dt.weekday() >= 5  # Saturday=5, Sunday=6

        tod_factor = time_of_day_factor(hour_frac, is_weekend)

        # Advance shared state machines
        weather.step()
        accident.step()
        roadwork.step()
        event.step()

        cond       = weather.condition
        temp_c     = weather.temp_c
        wdm        = WEATHER_DEMAND_MULT.get(cond, 1.0)
        density_wx = WEATHER_DENSITY_BOOST.get(cond, 1.0)
        cap_mult   = accident.capacity_multiplier * roadwork.capacity_multiplier
        event_mult = EVENT_DEMAND_MULT if event.active else 1.0

        # Hot weather: additional midday demand boost (11h - 15h)
        hot_boost = 1.12 if (cond == "Hot" and 11.0 <= hour_frac <= 15.0) else 1.0

        # Compute per-approach demand
        raw_demand: dict[str, float] = {}
        for ap in APPROACHES:
            s = yolo_stats[ap]

            # Mean demand from calibrated peak target shaped by time-of-day
            mean = PEAK_DEMAND_TARGETS[ap] * tod_factor * wdm * event_mult * hot_boost

            # Apply demand floor — no approach drops to zero even at 3am
            mean = max(mean, DEMAND_FLOOR[ap])

            # Noise scaled by YOLO coefficient of variation
            yolo_cv   = s["yolo_std_count"] / max(s["yolo_mean_count"], 0.1)
            noise_std = mean * max(NOISE_FRACTION, yolo_cv * 0.4)
            noise_std = max(noise_std, 0.5)

            arrivals = max(0.0, float(np_rng.normal(mean, noise_std)))
            raw_demand[ap] = arrivals

        greens = alloc_green(raw_demand)

        # Per-approach metrics
        for ap in APPROACHES:
            s        = yolo_stats[ap]
            arrivals = raw_demand[ap]
            green_s  = greens[ap]

            # Effective capacity this tick (vehicles/min)
            cap_per_tick = sat_flow_per_tick(ap) * (green_s / CYCLE_SECONDS) * cap_mult

            # Queue dynamics
            q          = queues[ap]
            q         += arrivals
            departures = min(q, cap_per_tick)
            q         -= departures
            queues[ap] = max(0.0, q)

            queue_int = int(math.ceil(queues[ap]))

            # Density: queue-relative with weather boost
            max_q        = sat_flow_per_tick(ap) * 2.0
            base_density = (queues[ap] / max(max_q, 1.0)) * 100.0 * density_wx
            dn           = float(np_rng.normal(0, DENSITY_NOISE_STD_PCT))
            density_pct  = round(max(0.0, min(100.0, base_density + dn)), 2)

            speed    = compute_speed(density_pct, cond, s["yolo_mean_speed"], rng)
            wait_min = compute_wait_time(queues[ap], speed, density_pct)
            volume_vph = round(arrivals * 60.0, 2)

            rows.append({
                "timestamp_wib":       dt.isoformat(),
                "tick":                tick,
                "intersectionId":      INTERSECTION_ID,
                "approach":            ap,
                "vehicle_count_1min":  int(round(arrivals)),
                "volume_veh_per_hour": volume_vph,
                "avg_speed_kmh":       speed,
                "queue_length_veh":    queue_int,
                "wait_time_min":       wait_min,
                "green_seconds":       green_s,
                "density_percent":     density_pct,
                "weather_condition":   cond,
                "weather_temp_c":      temp_c,
                "accident_count":      int(accident.active),
                "roadwork_flag":       int(roadwork.active),
                "event_flag":          int(event.active),
                "target_volume_15m":   None,
                "target_volume_2h":    None,
                "target_volume_4h":    None,
            })

        # Progress log every day
        if (tick + 1) % 1440 == 0:
            day = (tick + 1) // 1440
            log.info("  Day %d/7 complete (%d rows so far)", day, len(rows))

    df = pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Build target labels: future volume_veh_per_hour per approach
    # ------------------------------------------------------------------
    log.info("Building target labels...")
    for ap in APPROACHES:
        mask = df["approach"] == ap
        sub  = df.loc[mask, "volume_veh_per_hour"].reset_index(drop=True)

        df.loc[mask, "target_volume_15m"] = sub.shift(-HORIZON_15M).ffill().values
        df.loc[mask, "target_volume_2h"]  = sub.shift(-HORIZON_2H).ffill().values
        df.loc[mask, "target_volume_4h"]  = sub.shift(-HORIZON_4H).ffill().values

    for col in ("target_volume_15m", "target_volume_2h", "target_volume_4h"):
        df[col] = df[col].round(2)

    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(df: pd.DataFrame) -> bool:
    """Run final validation checks. Returns True if all pass."""
    passed = True
    checks = {
        "row_count == 40320":           len(df) == 40320,
        "no negative vehicle_count":    (df["vehicle_count_1min"] >= 0).all(),
        "no negative queue":            (df["queue_length_veh"] >= 0).all(),
        "density in [0, 100]":          df["density_percent"].between(0, 100).all(),
        "speed >= 10 kmh":              (df["avg_speed_kmh"] >= 10).all(),
        "no null target_volume_15m":    df["target_volume_15m"].notna().all(),
        "no null target_volume_2h":     df["target_volume_2h"].notna().all(),
        "no null target_volume_4h":     df["target_volume_4h"].notna().all(),
        "4 unique approaches":          df["approach"].nunique() == 4,
        "no null timestamps":           df["timestamp_wib"].notna().all(),
        "intersectionId consistent":    (df["intersectionId"] == INTERSECTION_ID).all(),
        "weather values valid":         df["weather_condition"].isin(WEATHER_CONDITIONS).all(),
        "N vehicle_count always >= 1":  (df[df["approach"]=="N"]["vehicle_count_1min"] >= 1).mean() > 0.95,
        "S vehicle_count always >= 1":  (df[df["approach"]=="S"]["vehicle_count_1min"] >= 1).mean() > 0.95,
        "peak volume N > 800 vph":      df[df["approach"]=="N"]["volume_veh_per_hour"].max() > 800,
        "peak volume S > 800 vph":      df[df["approach"]=="S"]["volume_veh_per_hour"].max() > 800,
    }

    log.info("--- Validation Results ---")
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        log.info("  [%s] %s", status, check)
        if not result:
            passed = False

    return passed


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("HYBRID TRAFFIC DATASET SUMMARY  —  Traffix.id")
    print("=" * 65)
    print(f"Intersection : {INTERSECTION_ID}")
    print(f"Location     : {LOCATION_NAME}")
    print(f"Total rows   : {len(df):,}")
    print(f"Approaches   : {sorted(df['approach'].unique().tolist())}")
    print(f"Time range   : {df['timestamp_wib'].iloc[0]}")
    print(f"           ->  {df['timestamp_wib'].iloc[-1]}")

    print("\n[Weather distribution]")
    wc          = df.drop_duplicates(subset=["tick"])["weather_condition"].value_counts()
    total_ticks = len(df) // 4
    for cond, count in wc.items():
        print(f"  {cond:8s}: {count:5d} ticks  ({count / total_ticks * 100:.1f}%)")

    print("\n[Per-approach vehicle count & volume]")
    print(f"  {'AP':<4} {'mean_veh':>9} {'max_veh':>8} {'min_veh':>8} {'mean_vol':>10} {'max_vol':>9}")
    for ap in APPROACHES:
        sub = df[df["approach"] == ap]
        vc  = sub["vehicle_count_1min"]
        vv  = sub["volume_veh_per_hour"]
        print(f"  {ap:<4} {vc.mean():>9.1f} {vc.max():>8d} {vc.min():>8d} {vv.mean():>10.0f} {vv.max():>9.0f}")

    print("\n[Global statistics]")
    for label, col in [
        ("Vehicle count", "vehicle_count_1min"),
        ("Volume vph",    "volume_veh_per_hour"),
        ("Density %",     "density_percent"),
        ("Speed km/h",    "avg_speed_kmh"),
        ("Queue veh",     "queue_length_veh"),
    ]:
        s = df[col].describe()
        print(f"  {label:<16}: mean={s['mean']:>7.2f}  std={s['std']:>7.2f}  "
              f"min={s['min']:>6.1f}  max={s['max']:>7.1f}")

    print("\n[Incidents]")
    print(f"  accident_count > 0 : {(df['accident_count'] > 0).sum():,} rows")
    print(f"  roadwork_flag  = 1 : {(df['roadwork_flag'] > 0).sum():,} rows")
    print(f"  event_flag     = 1 : {(df['event_flag'] > 0).sum():,} rows")

    print("\n[Preview — first 8 rows]")
    cols = [
        "timestamp_wib", "approach", "vehicle_count_1min",
        "volume_veh_per_hour", "density_percent", "avg_speed_kmh",
        "queue_length_veh", "weather_condition",
    ]
    print(df[cols].head(8).to_string(index=False))
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hybrid Traffic Dataset Generator v2 — Traffix.id"
    )
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
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    # Resolve input path (support running from any working directory)
    input_path = args.input
    if not os.path.exists(input_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate  = os.path.join(script_dir, args.input)
        if os.path.exists(candidate):
            input_path = candidate
        else:
            log.error("Input file not found: %s", args.input)
            sys.exit(1)

    log.info("Input  : %s", input_path)
    log.info("Output : %s", args.output)
    log.info("Seed   : %d", args.seed)

    # Load YOLO calibration
    yolo_stats = load_yolo_stats(input_path)

    # Generate dataset
    df = generate(yolo_stats=yolo_stats, seed=args.seed)

    # Validate
    valid = validate(df)
    if not valid:
        log.warning("Some validation checks FAILED — review data before LSTM training.")
    else:
        log.info("All validation checks passed.")

    # Print summary
    print_summary(df)

    # Save
    output_path = args.output
    out_dir     = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(output_path, index=False)

    log.info("Saved %d rows -> %s", len(df), output_path)
    log.info("Done. Dataset ready for LSTM preprocessing and training.")


if __name__ == "__main__":
    main()
