"""Hybrid traffic CSV dataset loader for simulation ingestion."""

from collections.abc import Iterator
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from core.config import settings
from core.paths import resolve_asset_path
from sim.dataset_adapter import prepare_hybrid_traffic_dataframe
from sim.dataset_models import DatasetMetadata, DatasetRow


class DatasetLoaderError(Exception):
    """Base exception for hybrid traffic dataset loader failures."""


class DatasetSchemaError(DatasetLoaderError):
    """Raised when the hybrid traffic dataset schema is invalid."""


class DatasetNotFoundError(DatasetLoaderError):
    """Raised when the configured hybrid traffic dataset file is missing."""


class HybridTrafficDatasetLoader:
    """Lazy cached loader for `hybrid_traffic_7d.csv`."""

    REQUIRED_COLUMNS = (
        "timestamp",
        "intersection_id",
        "vehicle_count",
        "avg_speed",
        "occupancy_rate",
        "queue_length",
        "weather_condition",
        "temperature_celsius",
    )

    def __init__(self, dataset_path: str | Path | None = None) -> None:
        """Initialize the dataset loader.

        Args:
            dataset_path: Optional path override for testing or tooling.
        """
        self._dataset_path = Path(
            dataset_path or settings.hybrid_traffic_dataset_path,
        )
        self._dataframe: DataFrame | None = None

    @property
    def dataset_path(self) -> Path:
        """Return the resolved dataset path.

        Returns:
            Absolute path to the configured dataset.
        """
        configured = str(self._dataset_path)
        if Path(configured).is_absolute():
            return Path(configured)
        return resolve_asset_path(configured)

    def load_dataset(self) -> DataFrame:
        """Load and cache the hybrid traffic dataset.

        Returns:
            Cached pandas DataFrame with parsed UTC timestamps.

        Raises:
            DatasetNotFoundError: If the configured CSV file is missing.
            DatasetSchemaError: If required columns or timestamps are invalid.
        """
        if self._dataframe is not None:
            return self._dataframe.copy()

        path = self.dataset_path
        if not path.exists():
            raise DatasetNotFoundError(f"Dataset file not found: {path}")

        raw_dataframe = pd.read_csv(path)
        dataframe = prepare_hybrid_traffic_dataframe(raw_dataframe)
        self.validate_schema(dataframe)

        dataframe = dataframe.copy()
        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            utc=True,
            errors="coerce",
        )
        if dataframe["timestamp"].isna().any():
            raise DatasetSchemaError("Dataset contains invalid timestamps")

        dataframe["intersection_id"] = dataframe["intersection_id"].astype(str)
        dataframe = dataframe.sort_values(
            by=["timestamp", "intersection_id"],
        ).reset_index(drop=True)

        self._dataframe = dataframe
        return dataframe.copy()

    def validate_schema(self, dataframe: DataFrame) -> None:
        """Validate required dataset columns.

        Args:
            dataframe: DataFrame to validate.

        Raises:
            DatasetSchemaError: If one or more required columns are missing.
        """
        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise DatasetSchemaError(f"Missing required columns: {missing}")

    def _get_loaded_dataframe(self) -> DataFrame:
        """Return the cached DataFrame, loading it on first access.

        Returns:
            Cached DataFrame copy.
        """
        return self.load_dataset()

    def _row_from_record(self, record: pd.Series) -> DatasetRow:
        """Convert a pandas row into a typed dataset row.

        Args:
            record: DataFrame row.

        Returns:
            Typed dataset row.
        """
        return DatasetRow(
            timestamp=record["timestamp"].to_pydatetime(),
            intersection_id=str(record["intersection_id"]),
            vehicle_count=int(record["vehicle_count"]),
            avg_speed=float(record["avg_speed"]),
            occupancy_rate=float(record["occupancy_rate"]),
            queue_length=int(record["queue_length"]),
            weather_condition=str(record["weather_condition"]),
            temperature_celsius=float(record["temperature_celsius"]),
            target_volume_15m=self._optional_float(record, "target_volume_15m"),
            target_volume_2h=self._optional_float(record, "target_volume_2h"),
            target_volume_4h=self._optional_float(record, "target_volume_4h"),
        )

    def _optional_float(self, record: pd.Series, column: str) -> float | None:
        """Return a float column when present and non-null.

        Args:
            record: DataFrame row.
            column: Column name to read.

        Returns:
            Float value or None.
        """
        if column not in record.index:
            return None
        value = record[column]
        if pd.isna(value):
            return None
        return float(value)

    def get_rows(self) -> list[DatasetRow]:
        """Return all dataset rows as typed Pydantic models.

        Returns:
            List of typed dataset rows.
        """
        dataframe = self._get_loaded_dataframe()
        return [
            self._row_from_record(record)
            for _, record in dataframe.iterrows()
        ]

    def get_rows_by_intersection(
        self,
        intersection_id: str,
    ) -> list[DatasetRow]:
        """Return typed rows for one intersection.

        Args:
            intersection_id: Intersection identifier to filter by.

        Returns:
            List of typed dataset rows for the requested intersection.
        """
        dataframe = self._get_loaded_dataframe()
        filtered = dataframe[dataframe["intersection_id"] == intersection_id]
        return [
            self._row_from_record(record)
            for _, record in filtered.iterrows()
        ]

    def iter_rows(self) -> Iterator[DatasetRow]:
        """Yield dataset rows sequentially in timestamp order.

        Yields:
            Typed dataset rows in replay order.
        """
        dataframe = self._get_loaded_dataframe()
        for _, record in dataframe.iterrows():
            yield self._row_from_record(record)

    def get_latest_timestamp(self) -> pd.Timestamp | None:
        """Return the latest timestamp in the loaded dataset.

        Returns:
            Latest dataset timestamp, or None when dataset is empty.
        """
        dataframe = self._get_loaded_dataframe()
        if dataframe.empty:
            return None
        return dataframe["timestamp"].max()

    def get_dataset_metadata(self) -> DatasetMetadata:
        """Return summary metadata for the loaded dataset.

        Returns:
            Dataset metadata including row count and time range.
        """
        dataframe = self._get_loaded_dataframe()
        if dataframe.empty:
            return DatasetMetadata(
                rows=0,
                intersections=0,
                start_time=None,
                end_time=None,
                time_resolution_minutes=0,
            )

        timestamps = dataframe["timestamp"].drop_duplicates().sort_values()
        resolution = 0
        if len(timestamps) > 1:
            deltas = timestamps.diff().dropna()
            resolution = int(deltas.median().total_seconds() // 60)

        return DatasetMetadata(
            rows=int(len(dataframe)),
            intersections=int(dataframe["intersection_id"].nunique()),
            start_time=dataframe["timestamp"].min().to_pydatetime(),
            end_time=dataframe["timestamp"].max().to_pydatetime(),
            time_resolution_minutes=resolution,
        )
