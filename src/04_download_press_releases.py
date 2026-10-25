"""
04_download_press_releases.py
Step 1d: download every press release (the EX-99 exhibit), extract its text,
and store filings and texts in a SQLite database.
"""
import sqlite3
import time
import warnings

import pandas as pd
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from config import HEADERS, PROCESSED, PROJECT_ROOT, RAW

# A few exhibits are XML-shaped; reading them as HTML still extracts the text fine
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

CACHE = RAW / "press_releases"
CACHE.mkdir(parents=True, exist_ok=True)
DB_PATH = PROCESSED / "earnings.db"
pd.set_option("display.max_colwidth", 200)   # show long headlines in printouts


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
        time.sleep(5 * attempt)
    r.raise_for_status()


def html_to_text(html):
    """Remove HTML tags and squeeze all whitespace into single spaces."""
    soup = BeautifulSoup(html, "lxml")
    return " ".join(soup.get_text(" ").split())


# 1. Filings that have a press release (the 12 without one are dropped)
filings = pd.read_csv(PROCESSED / "earnings_filings_indexed.csv", dtype={"cik": str})
filings = filings.dropna(subset=["exhibit_url"])
print(f"{len(filings)} filings with a press release\n")

# 2. Create the tables from the schema file, then fill the filings table
con = sqlite3.connect(DB_PATH)
con.executescript((PROJECT_ROOT / "sql" / "01_schema.sql").read_text(encoding="utf-8"))

columns = ["accessionNumber", "ticker", "company", "segment", "cik", "filingDate",
           "accepted_ny", "items", "exhibit_type", "exhibit_url"]
# INSERT OR REPLACE: rerunning overwrites a row instead of duplicating it
con.executemany("INSERT OR REPLACE INTO filings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                filings[columns].itertuples(index=False, name=None))
con.commit()

# 3. Download each press release, extract its text and store it
for i, f in enumerate(filings.itertuples(), start=1):
    if f.exhibit_url.lower().endswith(".pdf"):
        print(f"  Skipped PDF: {f.ticker} {f.filingDate}")
        continue
    try:
        html = get_html(f.exhibit_url, CACHE / f"{f.accessionNumber}.htm")
    except Exception as e:                   # one bad download must not stop the run
        print(f"  Failed {f.ticker} {f.accessionNumber}: {e}")
        continue

    words = html_to_text(html).split()
    con.execute("INSERT OR REPLACE INTO press_releases VALUES (?, ?, ?, ?)",
                (f.accessionNumber, " ".join(words[:60]), len(words), " ".join(words)))
    if i % 100 == 0:
        con.commit()                         # save progress every 100 releases
        print(f"{i} of {len(filings)} done")
con.commit()

# 4. Check the result with SQL
print("\nReleases stored per company:")
print(pd.read_sql("""
    SELECT f.ticker,
           COUNT(p.accession_number) AS releases,
           ROUND(AVG(p.n_words))     AS avg_words
    FROM filings f
    LEFT JOIN press_releases p USING (accession_number)
    GROUP BY f.ticker
    ORDER BY releases DESC
""", con).to_string(index=False))

for t in ["PNC", "HOOD"]:
    print(f"\n----- {t}: headlines -----")
    print(pd.read_sql("""
        SELECT f.filing_date, p.headline
        FROM filings f
        JOIN press_releases p USING (accession_number)
        WHERE f.ticker = ?
        ORDER BY f.filing_date DESC
        LIMIT 8
    """, con, params=(t,)).to_string(index=False))

con.close()