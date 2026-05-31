# Traffix Data Directory

This directory is reserved for backend runtime data used by simulation and
future ML inference blocks. Large CSV files are intentionally ignored by git.

## Primary Dataset: `hybrid_traffic_7d.csv`

- Source: Data team synthetic generation (`data_synthetic/generate_data_hybrid.py`)
- Coverage: 7 days of synthetic traffic data
- Time resolution: per-minute simulation ticks, with derived 15-minute and
  60-minute rolling features
- Used by: backend simulation tick loop as dummy vehicle count source

## Expected Schema

Confirm operational contracts with the Data team before implementing readers.
The table below keeps the original backend-facing expectation from Block 0.0.

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Observation time |
| intersection_id | int | Intersection identifier (1-4) |
| vehicle_count | int | Vehicles counted in interval |
| avg_speed | float | Average speed (km/h) |
| occupancy_rate | float | Lane occupancy ratio (0-1) |
| hour | int | Hour of day (0-23) |
| day_of_week | int | Day (0=Mon, 6=Sun) |
| is_peak_hour | bool | Peak hour flag |
| is_weekend | bool | Weekend flag |

## Current Data Team Columns

The current `data_process/feature_columns.json` artifact lists the following
model input features:

- `vehicle_count_1min`, `volume_veh_per_hour`, `avg_speed_kmh`
- `queue_length_veh`, `wait_time_min`, `green_seconds`, `density_percent`
- `weather_temp_c`, `accident_count`, `roadwork_flag`, `event_flag`
- `hour`, `minute`, `day`, `day_of_week`, `month`, `is_holiday`, `is_weekend`
- `hour_sin`, `hour_cos`, `delta_volume`
- `lag_1`, `lag_5`, `lag_15`, `lag_30`, `lag_60`
- `lag_speed_15`, `lag_queue_15`
- `roll_mean_15`, `roll_std_15`, `roll_min_15`, `roll_max_15`
- `roll_median_15`, `roll_mean_60`, `roll_std_60`, `roll_min_60`,
  `roll_max_60`
- `weather_condition_Clear`, `weather_condition_Cloudy`
- `weather_condition_Hot`, `weather_condition_Rain`

The current `data_dictionary.md` also documents target columns:
`target_volume_15m`, `target_volume_2h`, and `target_volume_4h`.

## Related Files

- `data_process/feature_columns.json` - authoritative model feature list
- `data_process/data_dictionary.md` - full schema documentation
- `data_process/aggregation_rules.md` - raw CCTV aggregation rules
- `data_synthetic/generate_data_hybrid.py` - synthetic generation script
