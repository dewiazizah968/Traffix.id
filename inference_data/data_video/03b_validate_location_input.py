from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(".")

METADATA_DIR = BASE_DIR / "metadata"

INPUT_CSV = METADATA_DIR / "frame_km_input.csv"
OUTPUT_CSV = METADATA_DIR / "video_metadata.csv"
VALIDATION_REPORT_CSV = METADATA_DIR / "location_validation_report.csv"


def clean_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none", "null"]:
        return ""

    return text


def normalize_location_type(value):
    text = clean_text(value).lower()

    aliases = {
        "km": "km",
        "kilometer": "km",
        "kilometre": "km",

        "gate": "gate",
        "gt": "gate",
        "gerbang": "gate",
        "gerbang tol": "gate",

        "unknown": "unknown",
        "tidak terbaca": "unknown",
        "unreadable": "unknown",
    }

    return aliases.get(text, text)


def normalize_km_text(value):
    """
    Membersihkan KM agar formatnya konsisten.
    Contoh:
    KM 25+500  -> 25+500
    25 + 500   -> 25+500
    04+600     -> 04+600
    """
    text = clean_text(value).upper()

    if not text:
        return ""

    text = text.replace("KM", "")
    text = text.replace(" ", "")
    text = text.replace(":", "")
    text = text.replace(";", "")

    return text


def km_text_to_decimal(km_text):
    """
    Konversi:
    25+500 -> 25.5
    04+600 -> 4.6
    10+000 -> 10.0
    """
    text = normalize_km_text(km_text)

    if not text:
        return ""

    match = re.match(r"^(\d+)\+(\d{1,3})$", text)

    if not match:
        return ""

    km = int(match.group(1))
    meter_text = match.group(2)

    # Supaya 5 dianggap 500 meter, 50 dianggap 500 meter, 500 tetap 500 meter.
    meter = int(meter_text.ljust(3, "0"))

    if meter >= 1000:
        return ""

    return round(km + (meter / 1000), 3)


def build_camera_label(location_type, location_text, km_text, ruas):
    location_type = normalize_location_type(location_type)
    location_text = clean_text(location_text)
    km_text = normalize_km_text(km_text)
    ruas = clean_text(ruas)

    if location_type == "km":
        if location_text:
            return location_text
        if km_text:
            return f"KM {km_text} {ruas}".strip()
        return ""

    if location_type == "gate":
        return location_text

    return location_text


def validate_manual_status(location_type, location_text, km_text):
    location_type = normalize_location_type(location_type)
    location_text = clean_text(location_text)
    km_text = normalize_km_text(km_text)

    if not location_type:
        return "need_location_type"

    if location_type == "km":
        if not km_text:
            return "need_km_input"

        km_decimal = km_text_to_decimal(km_text)

        if km_decimal == "":
            return "invalid_km_format"

        return "valid"

    if location_type == "gate":
        if not location_text:
            return "need_location_text"

        return "valid"

    if location_type == "unknown":
        return "need_review"

    return "invalid_location_type"


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {INPUT_CSV}. "
            "Pastikan kamu sudah menjalankan 03_select_best_frame.py "
            "dan sudah mengisi frame_km_input.csv."
        )

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")

    required_columns = [
        "location_type",
        "location_text",
        "km_text",
        "ruas",
        "video_file",
        "cctv_id",
        "timestamp_wib",
        "selected_frame_path",
        "selected_frame_second"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di frame_km_input.csv: {col}")

    # Normalisasi kolom input manual
    df["location_type"] = df["location_type"].apply(normalize_location_type)
    df["location_text"] = df["location_text"].apply(clean_text)
    df["km_text"] = df["km_text"].apply(normalize_km_text)

    # Isi otomatis km_decimal
    df["km_decimal"] = df["km_text"].apply(km_text_to_decimal)

    # Isi otomatis manual_status
    df["manual_status"] = df.apply(
        lambda row: validate_manual_status(
            row["location_type"],
            row["location_text"],
            row["km_text"]
        ),
        axis=1
    )

    # Buat camera_label otomatis
    df["camera_label"] = df.apply(
        lambda row: build_camera_label(
            row["location_type"],
            row["location_text"],
            row["km_text"],
            row["ruas"]
        ),
        axis=1
    )

    # Buat camera_key untuk identifikasi lokasi unik
    df["camera_key"] = df.apply(
        lambda row: f'{row["ruas"]}_{row["location_type"]}_{row["camera_label"]}'
        .lower()
        .replace(" ", "_")
        .replace("+", "plus"),
        axis=1
    )

    # Simpan hasil final
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    # Buat report validasi
    report = (
        df["manual_status"]
        .value_counts()
        .rename_axis("manual_status")
        .reset_index(name="count")
    )

    report.to_csv(VALIDATION_REPORT_CSV, index=False, encoding="utf-8-sig")

    print("[SUCCESS] Validasi input lokasi selesai.")
    print(f"[OUTPUT] Metadata final       : {OUTPUT_CSV}")
    print(f"[OUTPUT] Report validasi      : {VALIDATION_REPORT_CSV}")

    print("\nRingkasan manual_status:")
    print(report.to_string(index=False))

    invalid_df = df[df["manual_status"] != "valid"]

    if not invalid_df.empty:
        print("\n[WARNING] Masih ada baris yang perlu dicek:")
        print(
            invalid_df[
                [
                    "no",
                    "video_file",
                    "location_type",
                    "location_text",
                    "km_text",
                    "manual_status",
                    "notes"
                ]
            ].to_string(index=False)
        )
    else:
        print("\n[SUCCESS] Semua baris sudah valid.")


if __name__ == "__main__":
    main()