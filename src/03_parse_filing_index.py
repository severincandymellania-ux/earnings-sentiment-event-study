"""
03_parse_filing_index.py
Step 1c: open each earnings filing's index page on EDGAR and record
  - the "Accepted" time (New York time), which we trust over the API field
  - the press release exhibit (EX-99.1): its type, URL and description
"""
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import HEADERS, PROCESSED, RAW

CACHE = RAW / "index_pages"
CACHE.mkdir(parents=True, exist_ok=True)

# Companies label the press release slightly differently; checked in this order
PRESS_RELEASE_TYPES = ["EX-99.1", "EX-99.01", "EX-99"]


def get_html(url, cache_file, retries=3):
    """Return a page's HTML; reuse the cached copy. Retries on temporary errors."""
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    for attempt in range(1, retries + 1):
        time.sleep(0.15)                     # stay under 10 requests/second
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            cache_file.write_text(r.text, encoding="utf-8")
            return r.text
        print(f"  HTTP {r.status_code} on attempt {attempt}: {url}")
        time.sleep(5 * attempt)              # wait longer after each failure
    r.raise_for_status()


def parse_index(html):
    """Pull the Accepted time and the press release exhibit from an index page."""
    soup = BeautifulSoup(html, "lxml")

    # "Accepted" is a label (infoHead) followed by its value (info)
    accepted = None
    for head in soup.find_all("div", class_="infoHead"):
        if head.get_text(strip=True) == "Accepted":
            accepted = head.find_next_sibling("div", class_="info").get_text(strip=True)

    # Document table: columns are Seq, Description, Document, Type, Size
    exhibits = {}                            # document type -> (url, description)
    table = soup.find("table", class_="tableFile")
    rows = table.find_all("tr")[1:] if table else []   # [1:] skips the header row
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4 or cells[2].find("a") is None:
            continue
        doc_type = cells[3].get_text(strip=True).upper()
        href = cells[2].find("a")["href"].replace("/ix?doc=", "")
        exhibits.setdefault(doc_type, ("https://www.sec.gov" + href,
                                       cells[1].get_text(strip=True)))

    for doc_type in PRESS_RELEASE_TYPES:
        if doc_type in exhibits:
            url, desc = exhibits[doc_type]
            return accepted, doc_type, url, desc
    return accepted, None, None, None


# 1. Visit every filing's index page
filings = pd.read_csv(PROCESSED / "earnings_filings.csv", dtype={"cik": str})
results = []

for i, f in enumerate(filings.itertuples(), start=1):
    acc_nodash = f.accessionNumber.replace("-", "")
    url = (f"https://www.sec.gov/Archives/edgar/data/{int(f.cik)}/"
           f"{acc_nodash}/{f.accessionNumber}-index.htm")
    try:
        html = get_html(url, CACHE / f"{f.accessionNumber}.htm")
        results.append(parse_index(html))
    except Exception as e:                   # one bad page must not stop the whole run
        print(f"  Failed {f.ticker} {f.accessionNumber}: {e}")
        results.append((None, None, None, None))
    if i % 100 == 0:
        print(f"{i} of {len(filings)} done")

parsed = pd.DataFrame(results, index=filings.index,
                      columns=["accepted_ny", "exhibit_type", "exhibit_url", "exhibit_desc"])
filings = pd.concat([filings, parsed], axis=1)

# 2. Compare the API time with the index page time
api_time = pd.to_datetime(filings["acceptanceDateTime"]).dt.tz_localize(None)
index_time = pd.to_datetime(filings["accepted_ny"])
filings["api_gap_hours"] = (api_time - index_time).dt.total_seconds() / 3600

# 3. Save and summarise
filings.to_csv(PROCESSED / "earnings_filings_indexed.csv", index=False)

print("\nGap between API time and index page time (hours -> number of filings):")
print(filings["api_gap_hours"].round(1).value_counts().head())
print("\nPress release type found:")
print(filings["exhibit_type"].value_counts(dropna=False))
for t in ["PNC", "HOOD"]:
    print(f"\n----- {t}: exhibit descriptions -----")
    print(filings.loc[filings["ticker"] == t, ["filingDate", "exhibit_desc"]].tail(12).to_string())