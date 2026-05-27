"""Normalize Data team hybrid traffic CSV into loader-compatible rows."""

from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from sim.intersection_mapping import (
    DEMO_INTERSECTION_IDS,
    DEMO_INTERSECTION_SCALE,
    map_dataset_intersection_id,
)

CANONICAL_COLUMNS = (
    "timestamp",
    "intersection_id",
    "vehicle_count",
    "avg_speed",
    "occupancy_rate",
    "queue_length",
    "weather_condition",
    "temperature_celsius",
)

TARGET_COLUMNS = (
    "target_volume_15m",
    "target_volume_2h",
    "target_volume_4h",
)

_COLUMN_ALIASES: dict[str, str] = {
    "timestamp_wib": "timestamp",
    "timestamp_utc": "timestamp",
    "intersectionId": "intersection_id",
    "vehicle_count_1min": "vehicle_count",
    "avg_speed_kmh": "avg_speed",
    "density_percent": "density_percent",
    "queue_length_veh": "queue_length",
    "weather_temp_c": "temperature_celsius",
    "target_volume_15m": "target_volume_15m",
    "target_volume_2h": "target_volume_2h",
    "target_volume_4h": "target_volume_4h",
}


def _occupancy_from_density(density_percent: float) -> float:
    """Convert density percent to occupancy ratio in [0, 1].

    Args:
        density_percent: Lane density percentage from the dataset.

    Returns:
        Occupancy ratio clamped between 0 and 1.
    """
    if density_percent <= 1.0:
        return max(0.0, min(1.0, float(density_percent)))
    return max(0.0, min(1.0, density_percent / 100.0))


def normalize_raw_dataframe(dataframe: DataFrame) -> DataFrame:
    """Rename and derive canonical hybrid-traffic columns.

    Args:
        dataframe: Raw CSV DataFrame from the Data team.

    Returns:
        DataFrame with canonical column names.
    """
    renamed = dataframe.rename(
        columns={
            source: target
            for source, target in _COLUMN_ALIASES.items()
            if source in dataframe.columns
        },
    )

    if "occupancy_rate" not in renamed.columns and "density_percent" in renamed.columns:
        renamed["occupancy_rate"] = renamed["density_percent"].map(
            _occupancy_from_density,
        )

    if "occupancy_rate" not in renamed.columns:
        renamed["occupancy_rate"] = 0.0

    return renamed


def aggregate_approaches(dataframe: DataFrame) -> DataFrame:
    """Aggregate approach-level rows to one row per intersection timestamp.

    Args:
        dataframe: Normalized DataFrame that may include an ``approach`` column.

    Returns:
        Aggregated DataFrame with one row per timestamp and intersection.
    """
    if "approach" not in dataframe.columns:
        return dataframe

    group_columns = ["timestamp", "intersection_id"]
    aggregations: dict[str, str] = {
        "vehicle_count": "sum",
        "avg_speed": "mean",
        "occupancy_rate": "mean",
        "queue_length": "sum",
        "weather_condition": "first",
        "temperature_celsius": "first",
    }
    for target_column in TARGET_COLUMNS:
        if target_column in dataframe.columns:
            aggregations[target_column] = "mean"

    return (
        dataframe.groupby(group_columns, as_index=False)
        .agg(aggregations)
        .reset_index(drop=True)
    )


def expand_demo_intersections(dataframe: DataFrame) -> DataFrame:
    """Fan out a single dataset intersection across all demo state store IDs.

    Args:
        dataframe: Aggregated canonical DataFrame.

    Returns:
        DataFrame containing rows for INT-001 through INT-004.
    """
    unique_ids = set(dataframe["intersection_id"].astype(str).unique())
    if len(unique_ids) > 1:
        mapped = dataframe.copy()
        mapped["intersection_id"] = mapped["intersection_id"].map(
            lambda value: map_dataset_intersection_id(str(value)),
        )
        return mapped

    expanded_rows: list[dict[str, object]] = []
    for _, record in dataframe.iterrows():
        base_intersection = map_dataset_intersection_id(
            str(record["intersection_id"]),
        )
        for demo_id in DEMO_INTERSECTION_IDS:
            scale = DEMO_INTERSECTION_SCALE[demo_id]
            row = record.to_dict()
            row["intersection_id"] = demo_id
            row["vehicle_count"] = int(round(float(record["vehicle_count"]) * scale))
            row["queue_length"] = int(round(float(record["queue_length"]) * scale))
            row["avg_speed"] = round(float(record["avg_speed"]) * (2.0 - scale), 2)
            row["occupancy_rate"] = round(
                min(1.0, float(record["occupancy_rate"]) * scale),
                4,
            )
            for target_column in TARGET_COLUMNS:
                if target_column in row and row[target_column] is not None:
                    row[target_column] = round(float(row[target_column]) * scale, 2)
            if base_intersection != demo_id:
                row["source_intersection_id"] = base_intersection
            expanded_rows.append(row)

    return pd.DataFrame(expanded_rows)


def prepare_hybrid_traffic_dataframe(dataframe: DataFrame) -> DataFrame:
    """Run the full Data team CSV normalization pipeline.

    Args:
        dataframe: Raw CSV contents.

    Returns:
        Canonical, aggregated, demo-expanded DataFrame.
    """
    normalized = normalize_raw_dataframe(dataframe)
    aggregated = aggregate_approaches(normalized)
    return expand_demo_intersections(aggregated)
