from pathlib import Path
import pandas as pd

BASE_DIR = Path(".")

METADATA_DIR = BASE_DIR / "metadata"

INPUT_CSV = METADATA_DIR / "video_metadata.csv"
OUTPUT_CSV = METADATA_DIR / "unique_camera_locations.csv"
REPORT_CSV = METADATA_DIR / "unique_camera_locations_report.csv"


def clean_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none", "null"]:
        return ""

    return text


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {INPUT_CSV}. "
            "Pastikan kamu sudah menjalankan 03b_validate_location_input.py"
        )

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    required_columns = [
        "camera_key",
        "ruas",
        "location_type",
        "location_text",
        "km_text",
        "km_decimal",
        "camera_label",
        "manual_status"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di video_metadata.csv: {col}")

    invalid_df = df[df["manual_status"] != "valid"]

    if not invalid_df.empty:
        print("[WARNING] Masih ada data yang belum valid.")
        print(
            invalid_df[
                [
                    "video_file",
                    "location_type",
                    "location_text",
                    "km_text",
                    "manual_status"
                ]
            ].to_string(index=False)
        )
        raise ValueError(
            "Perbaiki dulu baris yang manual_status-nya belum valid "
            "sebelum membuat unique camera locations."
        )

    unique_df = (
        df[
            [
                "camera_key",
                "ruas",
                "location_type",
                "location_text",
                "km_text",
                "km_decimal",
                "camera_label"
            ]
        ]
        .drop_duplicates()
        .sort_values(["ruas", "location_type", "km_decimal", "camera_label"])
        .reset_index(drop=True)
    )

    unique_df.insert(0, "camera_id", [
        f"CAM_{i:03d}" for i in range(1, len(unique_df) + 1)
    ])

    # Kolom ini nanti kamu isi pada tahap 6
    unique_df["lat"] = ""
    unique_df["lon"] = ""
    unique_df["coordinate_source"] = ""
    unique_df["confidence"] = ""
    unique_df["coordinate_notes"] = ""

    # Hitung jumlah video per lokasi
    count_df = (
        df.groupby("camera_key")
        .size()
        .reset_index(name="video_count")
    )

    unique_df = unique_df.merge(count_df, on="camera_key", how="left")

    # Susun urutan kolom supaya enak dibaca
    column_order = [
        "camera_id",
        "camera_key",
        "ruas",
        "location_type",
        "location_text",
        "km_text",
        "km_decimal",
        "camera_label",
        "video_count",
        "lat",
        "lon",
        "coordinate_source",
        "confidence",
        "coordinate_notes"
    ]

    unique_df = unique_df[column_order]

    unique_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    report = (
        unique_df["location_type"]
        .value_counts()
        .rename_axis("location_type")
        .reset_index(name="count")
    )

    report.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    print("[SUCCESS] Daftar lokasi CCTV unik berhasil dibuat.")
    print(f"[OUTPUT] Lokasi unik : {OUTPUT_CSV}")
    print(f"[OUTPUT] Report      : {REPORT_CSV}")

    print(f"\nTotal video metadata : {len(df)}")
    print(f"Total lokasi unik    : {len(unique_df)}")

    print("\nRingkasan location_type:")
    print(report.to_string(index=False))

    print("\nTahap berikutnya:")
    print("- Buka metadata/unique_camera_locations.csv")
    print("- Isi kolom lat, lon, coordinate_source, confidence, dan coordinate_notes")
    print("- Jangan isi koordinat di video_metadata.csv")


if __name__ == "__main__":
    main()