"""
02_collect_earnings_filings.py
Step 1b: find every earnings release (8-K, Item 2.02) filed by the companies
in config.py between START_DATE and END_DATE.
Reads each company's full EDGAR filing history (including older pages),
caches every download in data/raw/submissions/, and saves one table to
data/processed/earnings_filings.csv.
"""
import json
import time

import pandas as pd
import requests

from config import COMPANIES, END_DATE, HEADERS, PROCESSED, RAW, START_DATE

CACHE = RAW / "submissions"
CACHE.mkdir(parents=True, exist_ok=True)


def get_json(url, cache_file):
    """Return JSON from EDGAR; reuse the cached copy if we downloaded it before."""
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    time.sleep(0.15)                       # stay under 10 requests/second
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    cache_file.write_text(r.text, encoding="utf-8")
    return r.json()


# 1. Ticker -> CIK lookup for all companies at once
lookup = get_json("https://www.sec.gov/files/company_tickers.json",
                  CACHE / "company_tickers.json")
lookup = pd.DataFrame(lookup.values())
ticker_to_cik = dict(zip(lookup["ticker"], lookup["cik_str"]))

missing = [t for t in COMPANIES if t not in ticker_to_cik]
if missing:
    print("Not found in the SEC ticker list (check these):", missing, "\n")

# 2. Collect earnings 8-Ks, company by company
all_filings = []

for ticker, segment in COMPANIES.items():
    if ticker not in ticker_to_cik:
        continue
    cik = str(ticker_to_cik[ticker]).zfill(10)

    sub = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json",
                   CACHE / f"CIK{cik}.json")
    pages = [pd.DataFrame(sub["filings"]["recent"])]

    # Older filings sit in extra pages; skip pages that end before our period
    for page in sub["filings"]["files"]:
        if page["filingTo"] < START_DATE:
            continue
        older = get_json(f"https://data.sec.gov/submissions/{page['name']}",
                         CACHE / page["name"])
        pages.append(pd.DataFrame(older))

    filings = pd.concat(pages, ignore_index=True)

    # Keep earnings releases inside the study period
    is_8k = filings["form"] == "8-K"
    has_202 = filings["items"].str.contains("2.02", regex=False, na=False)
    in_period = filings["filingDate"].between(START_DATE, END_DATE)
    earnings = filings[is_8k & has_202 & in_period].copy()

    earnings["ticker"] = ticker
    earnings["company"] = sub["name"]
    earnings["segment"] = segment
    earnings["cik"] = cik
    all_filings.append(earnings)
    print(f"{ticker:<5} {sub['name'][:35]:<35} {len(earnings):>3} earnings 8-Ks")

# 3. Combine all companies and save
cols = ["ticker", "company", "segment", "cik", "filingDate", "acceptanceDateTime",
        "accessionNumber", "items", "primaryDocument"]
result = (pd.concat(all_filings, ignore_index=True)[cols]
          .sort_values(["ticker", "filingDate"]))
result.to_csv(PROCESSED / "earnings_filings.csv", index=False)

print(f"\nTotal: {len(result)} earnings 8-Ks from {result['ticker'].nunique()} companies")
print("Saved to data/processed/earnings_filings.csv")