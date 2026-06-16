import csv
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

INPUT_TXT = Path("output_stage1_cctv") / "cctv_jasamarga_m3u8_links_only.txt"

OUTPUT_DIR = Path("output_stage2_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_CSV = OUTPUT_DIR / "recording_report.csv"

# Durasi rekam per CCTV.
# 120 = 2 menit
# 180 = 3 menit
RECORD_SECONDS = 180

MAX_STREAMS = None

WAIT_BETWEEN_RECORDINGS = 3

REFERER = "https://binamarga.pu.go.id/contents/cctv_tol/?id_ruas=jakarta-tangerang"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def check_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg belum terpasang atau belum terbaca di PATH. "
            "Install dulu dengan: winget install Gyan.FFmpeg"
        )

    return ffmpeg_path


def read_links(input_txt):
    if not input_txt.exists():
        raise FileNotFoundError(f"File input tidak ditemukan: {input_txt}")

    links = []

    with open(input_txt, "r", encoding="utf-8") as file:
        for line in file:
            url = line.strip()

            if not url:
                continue

            if ".m3u8" not in url.lower():
                continue

            if url not in links:
                links.append(url)

    return links


def safe_filename(text):
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in text)
    return safe[:120]


def record_stream_copy_mode(ffmpeg_path, url, output_file):
    """
    Mode utama: copy stream langsung.
    Lebih cepat dan tidak berat untuk laptop.
    """
    headers = (
        f"Referer: {REFERER}\r\n"
        f"Origin: https://binamarga.pu.go.id\r\n"
    )

    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "warning",

        "-user_agent", USER_AGENT,
        "-headers", headers,

        "-rw_timeout", "15000000",
        "-fflags", "+genpts",

        "-i", url,

        "-t", str(RECORD_SECONDS),
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",

        str(output_file),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result


def record_stream_reencode_mode(ffmpeg_path, url, output_file):
    """
    Mode cadangan jika mode copy gagal.
    Lebih berat, tetapi kadang lebih stabil untuk output MP4.
    """
    headers = (
        f"Referer: {REFERER}\r\n"
        f"Origin: https://binamarga.pu.go.id\r\n"
    )

    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "warning",

        "-user_agent", USER_AGENT,
        "-headers", headers,

        "-rw_timeout", "15000000",
        "-fflags", "+genpts",

        "-i", url,

        "-t", str(RECORD_SECONDS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",

        str(output_file),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result


def file_is_valid(output_file):
    if not output_file.exists():
        return False

    # Minimal 100 KB agar tidak dianggap file kosong/rusak.
    if output_file.stat().st_size < 100_000:
        return False

    return True


def main():
    ffmpeg_path = check_ffmpeg()
    links = read_links(INPUT_TXT)

    if not links:
        print("Tidak ada link .m3u8 yang ditemukan di file input.")
        return

    if MAX_STREAMS is not None:
        links = links[:MAX_STREAMS]

    print("Tahap 2 dimulai.")
    print(f"File input       : {INPUT_TXT}")
    print(f"Total stream     : {len(links)}")
    print(f"Durasi per video : {RECORD_SECONDS} detik")
    print(f"Output folder    : {OUTPUT_DIR}")
    print()

    report_rows = []

    for index, url in enumerate(links, start=1):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"cctv_{index:03d}_{timestamp}.mp4"
        output_file = OUTPUT_DIR / output_name

        print(f"[{index}/{len(links)}] Merekam stream:")
        print(url)
        print(f"Output: {output_file}")

        start_time = datetime.now()

        result = record_stream_copy_mode(ffmpeg_path, url, output_file)

        mode_used = "copy"
        status = "success" if result.returncode == 0 and file_is_valid(output_file) else "failed"

        if status == "failed":
            print("Mode copy gagal. Mencoba mode re-encode...")

            if output_file.exists():
                output_file.unlink()

            result = record_stream_reencode_mode(ffmpeg_path, url, output_file)

            mode_used = "re-encode"
            status = "success" if result.returncode == 0 and file_is_valid(output_file) else "failed"

        end_time = datetime.now()

        file_size_mb = 0

        if output_file.exists():
            file_size_mb = round(output_file.stat().st_size / (1024 * 1024), 2)

        error_message = result.stderr[-1000:] if result.stderr else ""

        report_rows.append({
            "no": index,
            "url": url,
            "output_file": str(output_file),
            "record_seconds": RECORD_SECONDS,
            "mode_used": mode_used,
            "status": status,
            "file_size_mb": file_size_mb,
            "started_at": start_time.isoformat(timespec="seconds"),
            "finished_at": end_time.isoformat(timespec="seconds"),
            "error_message": error_message,
        })

        if status == "success":
            print(f"Berhasil: {output_file} ({file_size_mb} MB)")
        else:
            print("Gagal merekam stream ini. Detail error disimpan di recording_report.csv")

        print("-" * 70)

        time.sleep(WAIT_BETWEEN_RECORDINGS)

    with open(REPORT_CSV, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=report_rows[0].keys())
        writer.writeheader()
        writer.writerows(report_rows)

    print()
    print("Tahap 2 selesai.")
    print(f"Video tersimpan di : {OUTPUT_DIR}")
    print(f"Laporan tersimpan  : {REPORT_CSV}")


if __name__ == "__main__":
    main()