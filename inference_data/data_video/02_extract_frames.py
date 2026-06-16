from pathlib import Path
import subprocess
import csv
import shutil
import pandas as pd

BASE_DIR = Path(".")

METADATA_DIR = BASE_DIR / "metadata"
INVENTORY_CSV = METADATA_DIR / "video_inventory.csv"

FRAME_DIR = BASE_DIR / "frames"
FRAME_DIR.mkdir(exist_ok=True)

FRAME_REPORT_CSV = METADATA_DIR / "frame_extraction_report.csv"

# Detik yang akan diambil dari setiap video
FRAME_SECONDS = [1, 3, 5]


def check_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path is None:
        raise RuntimeError(
            "FFmpeg belum terpasang atau belum terbaca di PATH. "
            "Install FFmpeg terlebih dahulu, lalu buka ulang terminal VS Code."
        )

    return ffmpeg_path


def extract_frame_with_fallback(ffmpeg_path, video_path, output_path, target_second):
    fallback_seconds = {
        1: [1, 0.5, 0],
        3: [3, 2, 1, 0.5],
        5: [5, 4, 3, 2, 1, 0.5],
    }

    seconds_to_try = fallback_seconds.get(target_second, [target_second, 1, 0.5, 0])

    last_error = ""

    for second in seconds_to_try:
        command = [
            ffmpeg_path,
            "-y",
            "-ss", str(second),
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",
            str(output_path)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return {
                "status": "success",
                "actual_second_used": second,
                "error_message": ""
            }

        last_error = result.stderr[-800:] if result.stderr else "Tidak ada stderr"

    return {
        "status": "failed",
        "actual_second_used": "",
        "error_message": last_error
    }


def safe_stem(filename):
    """
    Mengambil nama file tanpa ekstensi.
    Contoh:
    pagi_cctv_001_20260518_070935.mp4
    menjadi:
    pagi_cctv_001_20260518_070935
    """
    return Path(filename).stem


def main():
    ffmpeg_path = check_ffmpeg()

    if not INVENTORY_CSV.exists():
        raise FileNotFoundError(
            f"File inventory tidak ditemukan: {INVENTORY_CSV}. "
            "Jalankan dulu 01_create_video_inventory.py"
        )

    df = pd.read_csv(INVENTORY_CSV)

    required_columns = ["period_folder", "video_file", "video_path"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di video_inventory.csv: {col}")

    rows = []

    print(f"[INFO] Membaca inventory: {INVENTORY_CSV}")
    print(f"[INFO] Total video di inventory: {len(df)}")

    for _, row in df.iterrows():
        period = str(row["period_folder"]).strip()
        video_file = str(row["video_file"]).strip()
        video_path = Path(str(row["video_path"]).strip())

        if not video_path.exists():
            print(f"[MISSING] Video tidak ditemukan: {video_path}")

            for second in FRAME_SECONDS:
                rows.append({
                    "period": period,
                    "video_file": video_file,
                    "video_path": str(video_path),
                    "frame_second": second,
                    "frame_file": "",
                    "frame_path": "",
                    "status": "video_not_found",
                    "error_message": "Video path tidak ditemukan"
                })

            continue

        # Buat subfolder frame berdasarkan periode: frames/pagi, frames/siang, frames/malam
        period_frame_dir = FRAME_DIR / period
        period_frame_dir.mkdir(exist_ok=True)

        video_name_without_ext = safe_stem(video_file)

        for second in FRAME_SECONDS:
            frame_filename = f"{video_name_without_ext}_frame_{second}s.jpg"
            frame_path = period_frame_dir / frame_filename

            result = extract_frame_with_fallback(
                ffmpeg_path=ffmpeg_path,
                video_path=video_path,
                output_path=frame_path,
                target_second=second
            )

            status = result["status"]
            actual_second_used = result["actual_second_used"]
            error_message = result["error_message"]

            error_message = ""
            if status != "success":
                error_message = result.stderr[-800:] if result.stderr else "Tidak ada stderr"

            rows.append({
                "period": period,
                "video_file": video_file,
                "video_path": str(video_path),
                "frame_second": second,
                "actual_second_used": actual_second_used,
                "frame_file": frame_filename,
                "frame_path": str(frame_path),
                "status": status,
                "error_message": error_message
            })

            if status == "success":
                print(f"[OK] {video_file} -> {frame_path}")
            else:
                print(f"[FAILED] {video_file} frame {second}s")

    with open(FRAME_REPORT_CSV, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "period",
                "video_file",
                "video_path",
                "frame_second",
                "actual_second_used",
                "frame_file",
                "frame_path",
                "status",
                "error_message"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n[SUCCESS] Ekstraksi frame selesai.")
    print(f"[OUTPUT] Folder frame: {FRAME_DIR}")
    print(f"[OUTPUT] Report CSV: {FRAME_REPORT_CSV}")


if __name__ == "__main__":
    main()