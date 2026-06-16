"""Application settings loaded from environment variables for Traffix."""

from typing import Any

from pydantic import Field, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def _parse_csv_list(value: str) -> list[str]:
    """Parse a comma-separated string into a list.

    Args:
        value: Comma-separated environment value.

    Returns:
        List of stripped non-empty values.
    """
    return [item.strip() for item in value.split(",") if item.strip()]


class TraffixEnvSettingsSource(EnvSettingsSource):
    """Environment source with Traffix-specific value parsing."""

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        """Prepare raw environment values before Pydantic validation.

        Args:
            field_name: Settings field name being parsed.
            field: Pydantic field metadata.
            value: Raw environment value.
            value_is_complex: Whether Pydantic sees the field as complex.

        Returns:
            Parsed field value.
        """
        if field_name == "cors_origins" and isinstance(value, str):
            return _parse_csv_list(value)
        return super().prepare_field_value(
            field_name,
            field,
            value,
            value_is_complex,
        )


class TraffixDotEnvSettingsSource(DotEnvSettingsSource):
    """Dotenv source with Traffix-specific value parsing."""

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        """Prepare raw dotenv values before Pydantic validation.

        Args:
            field_name: Settings field name being parsed.
            field: Pydantic field metadata.
            value: Raw dotenv value.
            value_is_complex: Whether Pydantic sees the field as complex.

        Returns:
            Parsed field value.
        """
        if field_name == "cors_origins" and isinstance(value, str):
            return _parse_csv_list(value)
        return super().prepare_field_value(
            field_name,
            field,
            value,
            value_is_complex,
        )


class Settings(BaseSettings):
    """Runtime configuration for the Traffix backend.

    Values are loaded from `.env` when present and fall back to defaults that
    match `.env.example`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources used to populate configuration.

        Args:
            settings_cls: Settings class being constructed.
            init_settings: Values passed directly to the initializer.
            env_settings: Values loaded from process environment variables.
            dotenv_settings: Values loaded from `.env`.
            file_secret_settings: Values loaded from file secrets.

        Returns:
            Ordered tuple of settings sources.
        """
        return (
            init_settings,
            TraffixEnvSettingsSource(settings_cls),
            TraffixDotEnvSettingsSource(settings_cls),
            file_secret_settings,
        )

    # App
    app_name: str = Field(default="traffix-backend", description="Service name")
    app_version: str = Field(default="0.1.0", description="Semantic version")
    app_env: str = Field(default="development", description="Runtime environment")
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")
    log_level: str = Field(default="info", description="Uvicorn log level")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    # ML Model Paths
    lstm_15m_path: str = Field(
        default="../LSTM Training/artifacts/best_lstm_15m.keras",
        description="Path to the 15-minute LSTM model artifact",
    )
    lstm_2h_path: str = Field(
        default="../LSTM Training/artifacts/best_lstm_2h.keras",
        description="Path to the 2-hour LSTM model artifact",
    )
    lstm_4h_path: str = Field(
        default="../LSTM Training/artifacts/best_lstm_4h.keras",
        description="Path to the 4-hour LSTM model artifact",
    )
    lstm_config_path: str = Field(
        default="../LSTM Training/artifacts/best_config.json",
        description="Path to the LSTM training configuration artifact",
    )
    ml_auto_load: bool = Field(
        default=True,
        description="Attempt to load LSTM artifacts during startup",
    )
    ml_allow_fallback: bool = Field(
        default=True,
        description="Use dataset/heuristic predictions when Keras files are absent",
    )
    prediction_auto_refresh: bool = Field(
        default=True,
        description="Refresh AI predictions after each simulation tick",
    )
    feat_scaler_path: str = Field(
        default="../LSTM Training/artifacts/feat_scaler.joblib",
        description="Path to the feature scaler artifact",
    )
    target_scaler_path: str = Field(
        default="../LSTM Training/artifacts/target_scalers.joblib",
        description="Path to the target scalers artifact",
    )

    # Data
    dummy_data_path: str = Field(
        default="data/hybrid_traffic_7d.csv",
        description="Path to the synthetic traffic simulation dataset",
    )
    hybrid_traffic_dataset_path: str = Field(
        default="../data/data_synthetic/hybrid_traffic_7d.csv",
        description="Path to the hybrid traffic CSV dataset",
    )
    feature_columns_path: str = Field(
        default="../data/data_process/feature_columns.json",
        description="Path to the Data team feature column manifest",
    )
    prediction_output_path: str = Field(
        default="../inference/inference_lstm/traffix_lstm_inference_outputs/lstm_prediction_output.csv",
        description="Path to the latest LSTM video prediction output",
    )
    prediction_output_json_path: str = Field(
        default="../inference/inference_lstm/traffix_lstm_inference_outputs/lstm_prediction_output.json",
        description="Path to the latest LSTM video prediction JSON output",
    )
    yolo_vehicle_count_path: str = Field(
        default="../inference/inference_yolo/vehicle_count.csv",
        description="Path to the latest YOLO vehicle count CSV output",
    )

    # Simulation
    simulation_auto_start: bool = Field(
        default=True,
        description="Start the replay tick engine automatically on startup",
    )
    tick_interval_seconds: int = Field(
        default=2,
        description="Simulation tick interval in seconds",
    )
    sim_intersections: int = Field(
        default=4,
        description="Number of intersections in the simulation",
    )

    # Weather
    bmkg_api_url: str = Field(
        default="https://api.bmkg.go.id/publik/prakiraan-cuaca",
        description="BMKG public weather forecast API URL",
    )

    # Camera
    camera_input_enabled: bool = Field(
        default=False,
        description="Enable live camera input for YOLO integration",
    )
    max_cameras: int = Field(
        default=16,
        description="Maximum number of camera streams supported",
    )
    camera_metadata_path: str = Field(
        default="../inference_data/data_video/metadata/video_weather_data.csv",
        description="Path to validated CCTV video metadata with weather enrichment",
    )
    camera_video_root_path: str = Field(
        default="../inference_data/data_video/video_input",
        description="Path to backend-hosted CCTV video files",
    )
    camera_video_library_url: str = Field(
        default="https://drive.google.com/drive/folders/1qJQ_B9wZP_kuzXoqaEtjVzBwLJTw3a0g?usp=sharing",
        description="Fallback external video library URL",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Parse CORS origins from a comma-separated env value.

        Args:
            value: Raw value supplied by pydantic-settings.

        Returns:
            List of allowed CORS origins.
        """
        if isinstance(value, str):
            return _parse_csv_list(value)
        return value

    def get_lstm_paths(self) -> dict[str, str]:
        """Return mapping of horizon to model file path.

        Returns:
            Dict mapping horizon string to `.keras` file path.
        """
        return {
            "15m": self.lstm_15m_path,
            "2h": self.lstm_2h_path,
            "4h": self.lstm_4h_path,
        }


settings = Settings()
