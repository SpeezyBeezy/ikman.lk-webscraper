# ikman.lk-webscraper
A simple web scraper to export the product title, product price, ad link, upload time, and selling location from ikman.lk to a CSV file

## Features
- Extracts:
  - Title
  - Price
  - Link
  - Time listed
  - Location (category prefix removed, e.g. "Mobile Phones").
- Skips promoted/featured ads.
- Writes rows live into CSV (flush + fsync).
- Optional configurable delay between pages (default = 0, "ruthless mode").
- Command line input for start URL and number of pages.

## Requirements
Install dependencies with:

    pip install -r requirements.txt

Dependencies used:
- beautifulsoup4
- requests
- tqdm

(Other modules are from Python’s standard library.)

## Usage
Run the scraper:

    ikman webscraper.py

You will be prompted to enter:
1. The start URL (e.g. `https://ikman.lk/en/ads/sri-lanka/mobile-phones`)
2. The number of pages to scrape.

Output will be saved as:

    phones_YYYY-MM-DD_HH-MM-SS.csv

## Example

