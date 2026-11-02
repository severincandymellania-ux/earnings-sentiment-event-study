"""
07_clean_texts.py
Phase 2, step 2b: turn each earnings release into a list of clean narrative sentences.
  1. Remove the EDGAR file label at the start ("EX-99.1 2 file.htm ...")
  2. Split the text into sentences and bullet points
  3. Keep a sentence only if it is 8 to 80 words, mostly letters (drops number tables),
     not boilerplate (disclaimers, call details, legal and accounting definitions,
     contacts, links), AND uses performance language (rose, fell, higher, compared with...)
The performance-language rule keeps what we want instead of listing everything we
don't, because boilerplate comes in endless forms. Leftover boilerplate repeats word
for word every quarter, so it cancels out in the within-company comparison of Phase 4.
Stores the result in the sentences table of data/processed/earnings.db
"""
import re
import sqlite3
from collections import Counter

import pandas as pd

from config import PROCESSED, PROJECT_ROOT

DB_PATH = PROCESSED / "earnings.db"
pd.set_option("display.max_colwidth", 200)

# "EX-99.1 2 q32025earningsrelease.htm " at the very start of each text
PREFIX = re.compile(r"^EX-99(\.0?1)?\s+\d+\s+\S+\.(htm|html|txt)\s+", re.IGNORECASE)
# Split at a sentence end (. ! ? then a space and a capital letter) or at a bullet symbol
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"(])|\s*[•▪●■◦]\s*")
# Routine text that says nothing about how the quarter went
BOILERPLATE = re.compile(
    r"forward-looking statement|safe harbor|caution|"
    r"webcast|conference call|replay|dial[- ]in|passcode|access code|"
    r"registration statement|proxy statement|prospectus|form 10-[kq]|"
    r"reconcil|on page \d+|non-gaap financial measure|non-gaap presentation|"
    r"in accordance with gaap|in isolation|substitute for|"
    r"(is|are) calculated|(is|are) defined|as defined|preliminary estimate|"
    r"for more information|investor relations|media contact|www\.|https?://|@",
    re.IGNORECASE)
# Performance language: up, down, comparison and judgment words, in both directions
PERFORMANCE = re.compile(
    r"\b(increas\w*|decreas\w*|rose|rise|rising|fell|fall|falling|grew|grow\w*|"
    r"declin\w*|higher|lower|improv\w*|deteriorat\w*|gain\w*|loss\w*|"
    r"up|down|record|strong\w*|solid|weak\w*|worse|pressure\w*|challeng\w*|"
    r"compared (with|to)|versus|vs\.?|year[- ]over[- ]year|from the prior)\b",
    re.IGNORECASE)

dropped = Counter()                          # how many pieces each rule removed


def clean_sentences(text):
    """Return the narrative sentences of one release, in their original order."""
    text = PREFIX.sub("", text)
    kept = []
    for s in SPLIT.split(text):
        words = s.split()
        if not 8 <= len(words) <= 80:
            dropped["too short or too long (headings, tables)"] += 1
            continue
        chars = s.replace(" ", "")
        if sum(c.isalpha() for c in chars) / len(chars) < 0.6:
            dropped["mostly numbers"] += 1
            continue
        if BOILERPLATE.search(s):
            dropped["boilerplate"] += 1
            continue
        if not PERFORMANCE.search(s):
            dropped["no performance language"] += 1
            continue
        kept.append(s.strip())
    return kept


con = sqlite3.connect(DB_PATH)
con.executescript((PROJECT_ROOT / "sql" / "01_schema.sql").read_text(encoding="utf-8"))

# 1. Earnings releases only
releases = pd.read_sql("""
    SELECT f.accession_number, f.ticker, p.full_text
    FROM filings f
    JOIN press_releases p USING (accession_number)
    WHERE f.release_type = 'earnings'
""", con)

# 2. Clean every release and store its sentences (rebuilt from scratch on each run)
con.execute("DELETE FROM sentences")
rows = []
for r in releases.itertuples():
    for i, s in enumerate(clean_sentences(r.full_text)):
        rows.append((r.accession_number, i, s, len(s.split())))
con.executemany("INSERT INTO sentences VALUES (?, ?, ?, ?)", rows)
con.commit()

# 3. Check the result
counts = pd.read_sql("""
    SELECT accession_number, COUNT(*) AS n_sentences
    FROM sentences
    GROUP BY accession_number
""", con)
counts = releases[["accession_number", "ticker"]].merge(counts, how="left").fillna(0)

print(f"Releases: {len(releases)}   Sentences kept: {len(rows):,}")
print("\nPieces removed by each rule:")
for reason, n in dropped.most_common():
    print(f"  {reason:<42} {n:>9,}")

print("\nSentences per release:")
print(counts["n_sentences"].describe(percentiles=[0.1, 0.5, 0.9]).round(0).to_string())

few = counts[counts["n_sentences"] < 10]
print(f"\nReleases with fewer than 10 sentences: {len(few)}")
if len(few):
    print(few.groupby("ticker").size().sort_values(ascending=False).to_string())

print("\nTwenty random sentences, to check by eye:")
print(pd.read_sql("SELECT text FROM sentences ORDER BY RANDOM() LIMIT 20", con)
        .to_string(index=False))
con.close()