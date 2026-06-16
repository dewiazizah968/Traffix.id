from pathlib import Path
import pandas as pd

BASE_DIR = Path(".")
METADATA_DIR = BASE_DIR / "metadata"

INPUT_CSV = METADATA_DIR / "unique_camera_locations.csv"
OUTPUT_CSV = METADATA_DIR / "unique_camera_locations_validated.csv"
REPORT_CSV = METADATA_DIR / "coordinate_validation_report.csv"

# Bounding box kasar Jakarta-Tangerang dan sekitarnya.
# Ini bukan validasi presisi, hanya untuk menangkap salah input ekstrem.
LAT_MIN = -6.40
LAT_MAX = -5.95
LON_MIN = 106.40
LON_MAX = 106.95

VALID_CONFIDENCE = {"high", "medium", "low"}


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in ["nan", "none", "null"]:
        return ""
    return text


def to_float_or_none(value):
    text = clean_text(value)
    if not text:
        return None

    # Antisipasi kalau tidak sengaja pakai koma desimal
    text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def validate_row(row):
    issues = []

    lat = to_float_or_none(row.get("lat", ""))
    lon = to_float_or_none(row.get("lon", ""))

    coordinate_source = clean_text(row.get("coordinate_source", ""))
    confidence = clean_text(row.get("confidence", "")).lower()

    if lat is None:
        issues.append("lat_missing_or_invalid")

    if lon is None:
        issues.append("lon_missing_or_invalid")

    if lat is not None and not (LAT_MIN <= lat <= LAT_MAX):
        issues.append("lat_out_of_jakarta_tangerang_bbox")

    if lon is not None and not (LON_MIN <= lon <= LON_MAX):
        issues.append("lon_out_of_jakarta_tangerang_bbox")

    if not coordinate_source:
        issues.append("coordinate_source_missing")

    if not confidence:
        issues.append("confidence_missing")
    elif confidence not in VALID_CONFIDENCE:
        issues.append("confidence_invalid")

    if issues:
        return "need_review", "; ".join(issues)

    return "valid", ""


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {INPUT_CSV}. "
            "Pastikan tahap 5 sudah menghasilkan unique_camera_locations.csv."
        )

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    required_columns = [
        "camera_id",
        "camera_key",
        "ruas",
        "location_type",
        "location_text",
        "km_text",
        "km_decimal",
        "camera_label",
        "lat",
        "lon",
        "coordinate_source",
        "confidence",
        "coordinate_notes"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan: {col}")

    statuses = []
    issues_list = []

    for _, row in df.iterrows():
        status, issues = validate_row(row)
        statuses.append(status)
        issues_list.append(issues)

    df["coordinate_status"] = statuses
    df["coordinate_issues"] = issues_list

    # Normalisasi confidence
    df["confidence"] = df["confidence"].apply(lambda x: clean_text(x).lower())

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    report = (
        df["coordinate_status"]
        .value_counts()
        .rename_axis("coordinate_status")
        .reset_index(name="count")
    )
    report.to_csv(REPORT_CSV, index=False, encoding="utf-8-sig")

    print("[SUCCESS] Validasi koordinat selesai.")
    print(f"[OUTPUT] Koordinat tervalidasi : {OUTPUT_CSV}")
    print(f"[OUTPUT] Report validasi       : {REPORT_CSV}")

    print("\nRingkasan coordinate_status:")
    print(report.to_string(index=False))

    need_review_df = df[df["coordinate_status"] != "valid"]

    if not need_review_df.empty:
        print("\n[WARNING] Ada koordinat yang perlu dicek:")
        print(
            need_review_df[
                [
                    "camera_id",
                    "camera_label",
                    "lat",
                    "lon",
                    "coordinate_status",
                    "coordinate_issues"
                ]
            ].to_string(index=False)
        )
    else:
        print("\n[SUCCESS] Semua koordinat valid secara format dan area kasar.")


if __name__ == "__main__":
    main()