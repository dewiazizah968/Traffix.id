from pathlib import Path
import pandas as pd

BASE_DIR = Path(".")
METADATA_DIR = BASE_DIR / "metadata"

VIDEO_METADATA_CSV = METADATA_DIR / "video_metadata.csv"
CAMERA_COORDINATES_CSV = METADATA_DIR / "unique_camera_locations_validated.csv"

OUTPUT_CSV = METADATA_DIR / "video_metadata_with_coordinates.csv"
REPORT_CSV = METADATA_DIR / "video_coordinate_join_report.csv"


def main():
    if not VIDEO_METADATA_CSV.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {VIDEO_METADATA_CSV}")

    if not CAMERA_COORDINATES_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {CAMERA_COORDINATES_CSV}. "
            "Jalankan dulu 05_validate_camera_coordinates.py"
        )

    video_df = pd.read_csv(VIDEO_METADATA_CSV, dtype=str).fillna("")
    coord_df = pd.read_csv(CAMERA_COORDINATES_CSV, dtype=str).fillna("")

    required_video_cols = [
        "camera_key",
        "video_file",
        "timestamp_wib",
        "ruas",
        "location_type",
        "location_text",
        "km_text",
        "km_decimal",
        "camera_label"
    ]

    required_coord_cols = [
        "camera_key",
        "camera_id",
        "lat",
        "lon",
        "coordinate_source",
        "confidence",
        "coordinate_status",
        "coordinate_issues"
    ]

    for col in required_video_cols:
        if col not in video_df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di video_metadata.csv: {col}")

    for col in required_coord_cols:
        if col not in coord_df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di unique_camera_locations_validated.csv: {col}")

    coord_cols_to_join = [
        "camera_key",
        "camera_id",
        "lat",
        "lon",
        "coordinate_source",
        "confidence",
        "coordinate_notes",
        "coordinate_status",
        "coordinate_issues"
    ]

    merged_df = video_df.merge(
        coord_df[coord_cols_to_join],
        on="camera_key",
        how="left"
    )

    merged_df["join_coordinate_status"] = merged_df.apply(
        lambda row: "valid"
        if str(row.get("lat", "")).strip() != "" and str(row.get("lon", "")).strip() != ""
        else "missing_coordinate",
        axis=1
    )

    merged_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    report = (
        merged_df["join_coordinate_status"]
        .value_counts()
        .rename_axis("join_coordinate_status")
        .reset_index(name="count")
    )

    report.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    print("[SUCCESS] Join video metadata dengan koordinat selesai.")
    print(f"[OUTPUT] Metadata + koordinat : {OUTPUT_CSV}")
    print(f"[OUTPUT] Report join          : {REPORT_CSV}")

    print("\nRingkasan join_coordinate_status:")
    print(report.to_string(index=False))

    missing_df = merged_df[merged_df["join_coordinate_status"] != "valid"]

    if not missing_df.empty:
        print("\n[WARNING] Ada video yang belum punya koordinat:")
        print(
            missing_df[
                [
                    "video_file",
                    "camera_key",
                    "camera_label",
                    "join_coordinate_status"
                ]
            ].to_string(index=False)
        )
    else:
        print("\n[SUCCESS] Semua video sudah memiliki koordinat.")


if __name__ == "__main__":
    main()