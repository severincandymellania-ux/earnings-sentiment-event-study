"""
01_explore_edgar.py
Step 1a: explore EDGAR for one company (JPMorgan) before automating.
"""
import json
import time

import pandas as pd
import requests

from config import HEADERS, RAW   # shared settings (paths, User-Agent)

# 1. Ticker -> CIK (EDGAR's company ID)
r = requests.get("https://www.sec.gov/files/company_tickers.json",
                 headers=HEADERS, timeout=30)
r.raise_for_status()
tickers = pd.DataFrame(r.json().values())
print(tickers.head(), "\n")

jpm = tickers[tickers["ticker"] == "JPM"].iloc[0]
cik = str(jpm["cik_str"]).zfill(10)   # EDGAR wants 10 digits, zero-padded
print("JPMorgan CIK:", cik, "\n")

time.sleep(0.2)   # stay well under the SEC limit of 10 requests/second

# 2. Download JPMorgan's filing history and cache a raw copy
url = f"https://data.sec.gov/submissions/CIK{cik}.json"
r = requests.get(url, headers=HEADERS, timeout=30)
r.raise_for_status()
sub = r.json()
(RAW / f"submissions_{cik}.json").write_text(json.dumps(sub))

recent = pd.DataFrame(sub["filings"]["recent"])   # ~last 1,000 filings
print("Columns available:", recent.columns.tolist(), "\n")
print("Filings in 'recent':", len(recent))
# Older filings live in extra files; we fetch these in Step 1b
print("Older filing pages:", [f["name"] for f in sub["filings"]["files"]], "\n")

# 3. Keep earnings releases: form 8-K tagged with Item 2.02
eightk = recent[recent["form"] == "8-K"]
# regex=False: treat "2.02" as plain text ("." means "any character" in regex)
earnings = eightk[eightk["items"].str.contains("2.02", regex=False, na=False)]

cols = ["filingDate", "acceptanceDateTime", "accessionNumber", "items", "primaryDocument"]
print(earnings[cols].head(10).to_string())
print("\nEarnings 8-Ks found in 'recent':", len(earnings))