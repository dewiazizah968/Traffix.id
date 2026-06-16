from pathlib import Path
import csv
import re
from datetime import datetime

BASE_DIR = Path(".")
INPUT_DIR = BASE_DIR / "video_input"
METADATA_DIR = BASE_DIR / "metadata"
METADATA_DIR.mkdir(exist_ok=True)

OUTPUT_CSV = METADATA_DIR / "video_inventory.csv"

VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv"]
PERIODS = ["pagi", "siang", "malam"]

# Pola nama file:
# pagi_cctv_001_20260518_070935.mp4
filename_pattern = re.compile(
    r"^(pagi|siang|malam)_(cctv_\d+)_(\d{8})_(\d{6})\.(mp4|avi|mov|mkv)$",
    re.IGNORECASE
)

rows = []

for period in PERIODS:
    period_folder = INPUT_DIR / period

    if not period_folder.exists():
        print(f"[SKIP] Folder tidak ditemukan: {period_folder}")
        continue

    video_files = sorted([
        file for file in period_folder.iterdir()
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS
    ])

    print(f"[INFO] Folder {period}: {len(video_files)} video ditemukan")

    for video_file in video_files:
        match = filename_pattern.match(video_file.name)

        parsed_period = period
        cctv_id = ""
        date_raw = ""
        time_raw = ""
        timestamp_from_filename = ""
        filename_status = "valid"

        if match:
            parsed_period = match.group(1).lower()
            cctv_id = match.group(2).lower()
            date_raw = match.group(3)
            time_raw = match.group(4)

            try:
                dt = datetime.strptime(date_raw + time_raw, "%Y%m%d%H%M%S")
                timestamp_from_filename = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                filename_status = "invalid_datetime"
        else:
            filename_status = "invalid_filename_format"

        rows.append({
            "period_folder": period,
            "period_from_filename": parsed_period,
            "video_file": video_file.name,
            "video_path": str(video_file),
            "cctv_id": cctv_id,
            "date_raw": date_raw,
            "time_raw": time_raw,
            "timestamp_from_filename": timestamp_from_filename,
            "filename_status": filename_status
        })

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "period_folder",
            "period_from_filename",
            "video_file",
            "video_path",
            "cctv_id",
            "date_raw",
            "time_raw",
            "timestamp_from_filename",
            "filename_status"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("\n[SUCCESS] Video inventory berhasil dibuat.")
print(f"[OUTPUT] {OUTPUT_CSV}")
print(f"[INFO] Total video terdata: {len(rows)}")