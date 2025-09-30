#!/usr/bin/env python3
"""
ikman.lk scraper — live CSV writing, no sleep by default (ruthless mode).
Extracts: Title, Price, Link, Time listed, Location (strips category like "Mobile Phones")
Skips: promoted / featured ads (top-ads-container..., featured-card...)
Writes CSV live (flush + fsync per row).
"""
from bs4 import BeautifulSoup, Tag
import requests
import csv
from datetime import datetime
from tqdm import tqdm
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import os

# --- Config ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}
DELAY_BETWEEN_PAGES = 0.0  # seconds; set >0 to re-enable polite delay
# ----------------


def remove_page_param(url: str) -> str:
    p = urlparse(url)
    query = dict(parse_qsl(p.query, keep_blank_values=True))
    query.pop("page", None)
    new_query = urlencode(query)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))


def build_page_url(base_url: str, page_num: int) -> str:
    p = urlparse(base_url)
    query = dict(parse_qsl(p.query, keep_blank_values=True))
    query["page"] = str(page_num)
    new_query = urlencode(query)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))


def has_promoted_parent(tag: Tag) -> bool:
    for parent in tag.parents:
        if not isinstance(parent, Tag):
            continue
        classes = parent.get("class", []) or []
        for c in classes:
            if c.startswith("top-ads-container") or c.startswith("featured-card"):
                return True
    return False


def extract_ad_data(ad_tag: Tag) -> dict:
    title_tag = ad_tag.select_one("h2.heading--2eONR")
    title = title_tag.get_text(strip=True) if title_tag else (ad_tag.get("title") or "").strip()

    price_tag = ad_tag.select_one("div.price--3SnqI")
    price = price_tag.get_text(strip=True) if price_tag else "N/A"

    time_tag = ad_tag.select_one("div.updated-time--1DbCk")
    time_listed = time_tag.get_text(strip=True) if time_tag else "N/A"

    desc_tag = ad_tag.select_one("div.description--2-ez3")
    location = "N/A"
    if desc_tag:
        desc_text = desc_tag.get_text(strip=True)
        parts = [p.strip() for p in desc_text.split(",")]
        location = parts[0] if parts else desc_text

    href = ad_tag.get("href", "").strip()
    if href.startswith("http://") or href.startswith("https://"):
        link = href
    else:
        link = "https://ikman.lk" + href

    return {
        "Title": title,
        "Price": price,
        "Link": link,
        "Time": time_listed,
        "Location": location,
    }


def scrape_and_write_live(start_url: str, num_pages: int, csv_filename: str) -> int:
    base = remove_page_param(start_url)
    header = ["Title", "Price", "Link", "Time", "Location"]

    # open file and write header once
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        f.flush()
        os.fsync(f.fileno())

        total_written = 0

        for page in tqdm(range(1, num_pages + 1), desc="Pages", unit="page"):
            page_url = build_page_url(base, page)
            try:
                resp = requests.get(page_url, headers=HEADERS, timeout=20)
            except Exception as e:
                print(f"Failed to request page {page} ({page_url}): {e}")
                # continue to next page (no sleep required per request)
                continue

            if resp.status_code != 200:
                print(f"Warning: page {page} returned status {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            ad_anchors = soup.select("a.card-link--3ssYv.gtm-ad-item")

            for ad in tqdm(ad_anchors, desc=f"Page {page} ads", leave=False, unit="ad"):
                if has_promoted_parent(ad):
                    continue

                try:
                    ad_data = extract_ad_data(ad)
                except Exception:
                    continue

                if ad_data["Title"] and ad_data["Link"]:
                    writer.writerow(ad_data)
                    # flush and sync to ensure the CSV is updated on disk immediately
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        # fsync may fail on some filesystems; ignore if it does
                        pass
                    total_written += 1

            # optional politeness: only run if >0
            if DELAY_BETWEEN_PAGES > 0:
                from time import sleep
                sleep(DELAY_BETWEEN_PAGES)

    return total_written


def main():
    print("ikman.lk scraper — live CSV writing (no enforced delay)")
    start_url = input("Enter the start page URL (e.g. https://ikman.lk/en/ads/sri-lanka/mobile-phones): ").strip()
    if not start_url:
        print("No URL entered — exiting.")
        return

    try:
        num_pages = int(input("Enter number of pages to scrape (exact): ").strip())
        if num_pages < 1:
            raise ValueError()
    except ValueError:
        print("Invalid number of pages — must be a positive integer. Exiting.")
        return

    start_time = datetime.now()
    timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"phones_{timestamp}.csv"

    print(f"Scraping {num_pages} pages starting from {start_url}")
    written = scrape_and_write_live(start_url, num_pages, filename)
    print(f"\nDone. Scraped and wrote {written} ads into {filename}")


if __name__ == "__main__":
    main()
