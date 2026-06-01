from pathlib import Path
import re
import pandas as pd
from datetime import datetime

BASE_DIR = Path(".")

METADATA_DIR = BASE_DIR / "metadata"
FRAME_REPORT_CSV = METADATA_DIR / "frame_extraction_report.csv"

OUTPUT_CSV = METADATA_DIR / "frame_km_input.csv"
OUTPUT_HTML = METADATA_DIR / "frame_review.html"

FRAME_PRIORITY = [3, 5, 1]

FILENAME_PATTERN = re.compile(
    r"^(pagi|siang|malam)_(cctv_\d+)_(\d{8})_(\d{6})\.(mp4|avi|mov|mkv)$",
    re.IGNORECASE
)


def parse_video_filename(video_file):
    match = FILENAME_PATTERN.match(video_file)

    if not match:
        return {
            "period_from_filename": "",
            "cctv_id": "",
            "date_raw": "",
            "time_raw": "",
            "overlay_date": "",
            "overlay_time": "",
            "timestamp_wib": "",
            "filename_parse_status": "invalid_filename_format"
        }

    period = match.group(1).lower()
    cctv_id = match.group(2).lower()
    date_raw = match.group(3)
    time_raw = match.group(4)

    try:
        dt = datetime.strptime(date_raw + time_raw, "%Y%m%d%H%M%S")
        overlay_date = dt.strftime("%Y-%m-%d")
        overlay_time = dt.strftime("%H:%M:%S")
        timestamp_wib = dt.strftime("%Y-%m-%d %H:%M:%S")
        filename_parse_status = "valid"
    except ValueError:
        overlay_date = ""
        overlay_time = ""
        timestamp_wib = ""
        filename_parse_status = "invalid_datetime"

    return {
        "period_from_filename": period,
        "cctv_id": cctv_id,
        "date_raw": date_raw,
        "time_raw": time_raw,
        "overlay_date": overlay_date,
        "overlay_time": overlay_time,
        "timestamp_wib": timestamp_wib,
        "filename_parse_status": filename_parse_status
    }


def normalize_path_for_html(path_text):
    return str(path_text).replace("\\", "/")


def create_html_gallery(df, output_html):
    rows_html = []

    for _, row in df.iterrows():
        img_path = normalize_path_for_html(Path("..") / row["selected_frame_path"])

        rows_html.append(f"""
        <tr>
            <td>{row["no"]}</td>
            <td>{row["period"]}</td>
            <td>{row["video_file"]}</td>
            <td>{row["cctv_id"]}</td>
            <td>{row["timestamp_wib"]}</td>
            <td>{row["selected_frame_second"]}s</td>
            <td>
                <a href="{img_path}" target="_blank">
                    <img src="{img_path}" style="width: 430px; border: 1px solid #ccc;">
                </a>
            </td>
            <td>{row["location_type"]}</td>
            <td><b>{row["location_text"]}</b></td>
            <td><b>{row["km_text"]}</b></td>
            <td>{row["manual_status"]}</td>
        </tr>
        """)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Frame Review CCTV</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 24px;
                background: #f5f5f5;
            }}
            h1 {{
                margin-bottom: 8px;
            }}
            .note {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                padding: 12px;
                margin-bottom: 16px;
                line-height: 1.5;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: white;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                vertical-align: top;
                font-size: 13px;
            }}
            th {{
                background: #222;
                color: white;
                position: sticky;
                top: 0;
            }}
            img {{
                display: block;
            }}
        </style>
    </head>
    <body>
        <h1>Frame Review CCTV</h1>

        <div class="note">
            Gunakan halaman ini untuk membaca overlay pada frame CCTV.
            Buka file <b>metadata/frame_km_input.csv</b>, lalu isi kolom manual sesuai overlay.
            Jika overlay berbentuk <b>KM 25+500</b>, isi <b>location_type = km</b>, <b>location_text = KM 25+500</b>, dan <b>km_text = 25+500</b>.
            Jika overlay berbentuk <b>GT MERUYA 2B</b>, isi <b>location_type = gate</b>, <b>location_text = GT MERUYA 2B</b>, dan kosongkan <b>km_text</b>.
        </div>

        <table>
            <thead>
                <tr>
                    <th>No</th>
                    <th>Period</th>
                    <th>Video File</th>
                    <th>CCTV ID</th>
                    <th>Timestamp WIB</th>
                    <th>Frame</th>
                    <th>Selected Frame</th>
                    <th>Location Type</th>
                    <th>Location Text</th>
                    <th>KM Text</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </body>
    </html>
    """

    output_html.write_text(html, encoding="utf-8")


def main():
    if not FRAME_REPORT_CSV.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan: {FRAME_REPORT_CSV}. "
            "Jalankan dulu 02_extract_frames.py"
        )

    df = pd.read_csv(FRAME_REPORT_CSV)

    required_columns = [
        "period",
        "video_file",
        "frame_second",
        "frame_file",
        "frame_path",
        "status"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib tidak ditemukan di frame_extraction_report.csv: {col}")

    success_df = df[df["status"] == "success"].copy()

    if success_df.empty:
        raise ValueError("Tidak ada frame yang berhasil diekstrak. Cek kembali tahap 2.")

    rows = []

    grouped = success_df.groupby(["period", "video_file"], as_index=False)

    for (period, video_file), group in grouped:
        selected_row = None

        for second in FRAME_PRIORITY:
            candidate = group[group["frame_second"] == second]

            if not candidate.empty:
                selected_row = candidate.iloc[0]
                break

        if selected_row is None:
            selected_row = group.iloc[0]

        parsed = parse_video_filename(video_file)

        rows.append({
            "period": period,
            "period_from_filename": parsed["period_from_filename"],
            "cctv_id": parsed["cctv_id"],
            "overlay_date": parsed["overlay_date"],
            "overlay_time": parsed["overlay_time"],
            "timestamp_wib": parsed["timestamp_wib"],
            "ruas": "Jakarta-Tangerang",
            "video_file": video_file,
            "selected_frame_path": selected_row["frame_path"],
            "selected_frame_second": selected_row["frame_second"],
            "selected_frame_file": selected_row["frame_file"],

            # Kolom manual utama
            "location_type": "",
            "location_text": "",
            "km_text": "",

            # Diisi otomatis pada tahap berikutnya setelah km_text selesai
            "km_decimal": "",

            # Status validasi manual
            "manual_status": "need_location_input",
            "filename_parse_status": parsed["filename_parse_status"],
            "notes": ""
        })

    output_df = pd.DataFrame(rows)
    output_df = output_df.sort_values(["period", "video_file"]).reset_index(drop=True)
    output_df.insert(0, "no", range(1, len(output_df) + 1))

    output_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    create_html_gallery(output_df, OUTPUT_HTML)

    print("[SUCCESS] Tahap 3 berhasil dibuat.")
    print(f"[OUTPUT] CSV input lokasi : {OUTPUT_CSV}")
    print(f"[OUTPUT] HTML review      : {OUTPUT_HTML}")
    print(f"[INFO] Total video       : {len(output_df)}")

    print("\nDistribusi frame terpilih:")
    print(output_df["selected_frame_second"].value_counts().sort_index())

    print("\nKolom yang perlu kamu isi manual:")
    print("- location_type")
    print("- location_text")
    print("- km_text jika overlay berbentuk KM")
    print("- manual_status")
    print("- notes jika perlu")


if __name__ == "__main__":
    main()