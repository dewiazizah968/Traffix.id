import os
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import requests
from playwright.sync_api import sync_playwright


TARGET_PAGES = [
    {
        "source_name": "Bina Marga CCTV Tol Jakarta-Tangerang",
        "page_url": "https://binamarga.pu.go.id/contents/cctv_tol/?id_ruas=jakarta-tangerang",
    },
]

OUTPUT_DIR = Path("output_stage1_cctv")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_OUTPUT = OUTPUT_DIR / "cctv_jasamarga_m3u8_unique.csv"
TXT_OUTPUT = OUTPUT_DIR / "cctv_jasamarga_m3u8_links_only.txt"
RAW_OUTPUT = OUTPUT_DIR / "cctv_jasamarga_raw_m3u8_collected.csv"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def clean_url(url):
    if not url:
        return None

    url = url.strip()
    url = url.replace("\\/", "/")
    url = url.replace("\\u0026", "&")

    url = url.split('"')[0]
    url = url.split("'")[0]
    url = url.split("<")[0]
    url = url.split(">")[0]

    if url.startswith("data:"):
        return None

    return url


def extract_m3u8_from_text(text):
    if not text:
        return set()

    pattern = r"https?://[^\s\"'<>]+?\.m3u8[^\s\"'<>]*"
    found_urls = re.findall(pattern, text)

    cleaned_urls = set()

    for url in found_urls:
        cleaned = clean_url(url)
        if cleaned and ".m3u8" in cleaned.lower():
            cleaned_urls.add(cleaned)

    return cleaned_urls


def collect_performance_resources(page):
    urls = set()

    try:
        resources = page.evaluate("""
            () => performance.getEntriesByType('resource').map(e => e.name)
        """)

        for resource_url in resources:
            cleaned = clean_url(resource_url)
            if cleaned and ".m3u8" in cleaned.lower():
                urls.add(cleaned)

    except Exception:
        pass

    return urls


def should_click_element(text):
    if not text:
        return False

    text_upper = text.upper()

    keywords = [
        "CCTV",
        "KM",
        "GT",
        "JANGER",
        "JAKARTA",
        "TANGERANG",
        "MERAK",
        "CAMERA",
        "KAMERA",
    ]

    return any(keyword in text_upper for keyword in keywords)


def click_public_camera_elements(page, collected_urls):
    selectors = [
        "button",
        "a",
        "[role='button']",
        "[onclick]",
        ".card",
        ".item",
        ".cctv",
        ".camera",
    ]

    for selector in selectors:
        try:
            elements = page.locator(selector)
            count = min(elements.count(), 80)

            for i in range(count):
                try:
                    element = elements.nth(i)

                    if not element.is_visible():
                        continue

                    text = element.inner_text(timeout=1000).strip()

                    if not should_click_element(text):
                        continue

                    before_url = page.url

                    element.scroll_into_view_if_needed(timeout=2000)
                    time.sleep(0.5)

                    element.click(timeout=3000, force=True)
                    time.sleep(2)

                    collected_urls.update(collect_performance_resources(page))

                    html_after_click = page.content()
                    collected_urls.update(extract_m3u8_from_text(html_after_click))

                    if page.url != before_url:
                        page.go_back(wait_until="networkidle", timeout=15000)
                        time.sleep(2)

                except Exception:
                    continue

        except Exception:
            continue


def check_m3u8_status(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        }

        response = requests.get(url, headers=headers, timeout=15)
        content_type = response.headers.get("Content-Type", "")

        text_sample = response.text[:1000] if response.text else ""

        hls_detected = "#EXTM3U" in text_sample

        return {
            "status_code": response.status_code,
            "content_type": content_type,
            "hls_detected": hls_detected,
            "check_note": "OK" if response.status_code == 200 else "URL tidak selalu bisa dibuka langsung, tetapi tetap bisa menjadi stream untuk player/code",
        }

    except Exception as e:
        return {
            "status_code": None,
            "content_type": None,
            "hls_detected": False,
            "check_note": f"Gagal dicek langsung: {str(e)[:120]}",
        }


def collect_from_page(source_name, page_url):
    collected_urls = set()
    raw_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        def capture_request(request):
            url = clean_url(request.url)
            if url and ".m3u8" in url.lower():
                collected_urls.add(url)

        def capture_response(response):
            url = clean_url(response.url)
            if url and ".m3u8" in url.lower():
                collected_urls.add(url)

        page.on("request", capture_request)
        page.on("response", capture_response)

        print(f"\nMembuka halaman: {source_name}")
        print(page_url)

        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)

        time.sleep(4)

        html = page.content()
        collected_urls.update(extract_m3u8_from_text(html))
        collected_urls.update(collect_performance_resources(page))

        # for _ in range(8):
        #     page.mouse.wheel(0, 900)
        #     time.sleep(1.5)

        #     html_scroll = page.content()
        #     collected_urls.update(extract_m3u8_from_text(html_scroll))
        #     collected_urls.update(collect_performance_resources(page))

        # for _ in range(4):
        #     page.mouse.wheel(0, -900)
        #     time.sleep(1)

        # click_public_camera_elements(page, collected_urls)

        for _ in range(3):
            page.mouse.wheel(0, 900)
            time.sleep(1)

        html_scroll = page.content()
        collected_urls.update(extract_m3u8_from_text(html_scroll))
        collected_urls.update(collect_performance_resources(page))

        html_final = page.content()
        collected_urls.update(extract_m3u8_from_text(html_final))
        collected_urls.update(collect_performance_resources(page))

        browser.close()

    for url in collected_urls:
        raw_rows.append({
            "collected_at": now_iso(),
            "source_name": source_name,
            "page_url": page_url,
            "m3u8_url": url,
            "domain": urlparse(url).netloc,
        })

    return raw_rows


def main():
    all_rows = []

    for target in TARGET_PAGES:
        rows = collect_from_page(
            source_name=target["source_name"],
            page_url=target["page_url"],
        )
        all_rows.extend(rows)

    if not all_rows:
        print("\nTidak ada link .m3u8 yang ditemukan.")
        return

    raw_df = pd.DataFrame(all_rows)
    raw_df.to_csv(RAW_OUTPUT, index=False, encoding="utf-8-sig")

    unique_df = raw_df.drop_duplicates(subset=["m3u8_url"]).reset_index(drop=True)

    status_rows = []

    print("\nMengecek status link .m3u8...")

    for _, row in unique_df.iterrows():
        status = check_m3u8_status(row["m3u8_url"])
        status_rows.append(status)
        time.sleep(0.5)

    status_df = pd.DataFrame(status_rows)
    final_df = pd.concat([unique_df, status_df], axis=1)

    final_df.insert(0, "no", range(1, len(final_df) + 1))
    final_df["media_type"] = "HLS live stream playlist (.m3u8)"

    final_df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")

    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        for url in final_df["m3u8_url"]:
            f.write(url + "\n")

    print("\nTahap 1 selesai.")
    print(f"Total link .m3u8 mentah : {len(raw_df)}")
    print(f"Total link .m3u8 unik   : {len(final_df)}")
    print(f"File CSV utama          : {CSV_OUTPUT}")
    print(f"File TXT link saja      : {TXT_OUTPUT}")
    print(f"File raw cadangan       : {RAW_OUTPUT}")


if __name__ == "__main__":
    main()