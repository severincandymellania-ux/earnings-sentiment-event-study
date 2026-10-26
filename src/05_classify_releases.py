"""
05_classify_releases.py
Step 1e: decide which Item 2.02 filings are real quarterly earnings releases.
  1. Releases with fewer than 100 words (slides saved as images) -> 'no_text'
  2. Every other release gets an earnings score: points for earnings language in
     the first 300 words, penalties for signs of an extra in the first 60 words
  3. One release per company per quarter: within each company and calendar
     quarter, the highest-scoring filing (score >= 2) -> 'earnings'
  4. Everything else -> 'other'
  5. A few cases the rule cannot settle are decided by hand (MANUAL_DECISIONS),
     each checked by reading the text
  6. Gap check: lists rejected filings in quarters that have no earnings release
Writes release_type into the filings table and a review file to
data/processed/classification_review.csv
"""
import re
import sqlite3

import pandas as pd

from config import PROCESSED

DB_PATH = PROCESSED / "earnings.db"
pd.set_option("display.width", 250)

# Typical earnings language, searched in the first 300 words: +1 point per pattern
POSITIVE = [
    r"\b(first|second|third|fourth)\s+(fiscal\s+)?quarter",   # "Third Quarter"
    r"\b(1st|2nd|3rd|4th)\s+quarter",                          # "4th Quarter"
    r"\bq[1-4]\b|\bfq[1-4]|\b[1-4]q\d{2}\b",                  # "Q4-15", "FQ2'25", "1Q23"
    r"full[\s-]year",
    r"(quarter|year|q[1-4])\s+(and full year\s+)?(20\d\d\s+)?results",   # "Third Quarter 2022 Results"
    r"\b(reports|reported|announces|announced)\b.{0,80}\b(results|earnings|net income|net loss|eps)",
    r"net (income|loss)|diluted (eps|earnings)|earnings per (common )?share",
    r"earnings ?release|press ?release|shareholder letter|to our shareholders|fellow \w+ shareholders",
]

# Signs of an extra, searched only in the first 60 words (the headline area): -2 points each.
# Real releases may use these words in passing, e.g. "settlement of certain tax matters".
NEGATIVE = [
    r"\bconference\b(?!\s+call)",     # "conference" but not "conference call"
    r"\bforum\b|investor day|annual meeting",
    r"order routing",
    r"consent order|settlements? with|reach(es|ed)? (a )?settlement|tribunal",
    r"\brecast\b|financial data supplement",
]

# Cases the rule cannot settle, decided by reading the text: (ticker, filing date) -> (label, reason)
MANUAL_DECISIONS = {
    ("STT", "2019-07-19"): ("earnings", "Q2 2019 earnings release; file name '2q19earningspre'"),
    ("XYZ", "2023-11-02"): ("earnings", "Q3 2023 results published as a shareholder letter"),
    ("XYZ", "2024-05-02"): ("earnings", "Q1 2024 results published as a shareholder letter"),
    ("NTRS", "2017-10-18"): ("other", "CEO succession announcement, not an earnings release"),
}


def earnings_score(text):
    """Points for earnings language, minus penalties for an extra's headline."""
    text = text.lower()
    head = " ".join(text.split()[:60])       # extras announce themselves at the top
    score = sum(bool(re.search(p, text)) for p in POSITIVE)
    score -= 2 * sum(bool(re.search(p, head)) for p in NEGATIVE)
    return score


con = sqlite3.connect(DB_PATH)

# 1. Load filings with the first ~3,000 characters of each release
df = pd.read_sql("""
    SELECT f.accession_number, f.ticker, f.filing_date,
           p.n_words,
           substr(p.full_text, 1, 3000) AS opening
    FROM filings f
    JOIN press_releases p USING (accession_number)
""", con)

df["opening"] = df["opening"].fillna("").str.split().str[:300].str.join(" ")
df["score"] = df["opening"].apply(earnings_score)
df["quarter"] = pd.to_datetime(df["filing_date"]).dt.to_period("Q").astype(str)

# 2. Rule: no_text first, then the best filing per company and quarter
df["release_type"] = "other"
df["decided_by"] = "rule"
df.loc[df["n_words"] < 100, "release_type"] = "no_text"

candidates = df[df["release_type"] != "no_text"]
best = (candidates.sort_values(["score", "filing_date"], ascending=[False, True])
                  .groupby(["ticker", "quarter"])
                  .head(1))                  # top filing in each company-quarter
best = best[best["score"] >= 2]
df.loc[best.index, "release_type"] = "earnings"

# 3. Manual decisions override the rule
for (ticker, date), (label, reason) in MANUAL_DECISIONS.items():
    match = (df["ticker"] == ticker) & (df["filing_date"] == date)
    assert match.sum() == 1, f"Manual decision {ticker} {date} matches {match.sum()} filings"
    df.loc[match, ["release_type", "decided_by"]] = [label, "manual"]

# 4. Save the label into the database
try:
    con.execute("ALTER TABLE filings ADD COLUMN release_type TEXT")
except sqlite3.OperationalError:
    pass                                     # column already exists
con.executemany("UPDATE filings SET release_type = ? WHERE accession_number = ?",
                df[["release_type", "accession_number"]].itertuples(index=False, name=None))
con.commit()
con.close()

# 5. Summary and review file
print("Labels overall:")
print(df["release_type"].value_counts().to_string())
print(f"Decided by hand: {(df['decided_by'] == 'manual').sum()}\n")

print("Labels per company:")
per_company = df.pivot_table(index="ticker", columns="release_type",
                             values="accession_number", aggfunc="count", fill_value=0)
print(per_company.sort_values("earnings").to_string())

review = df[(df["release_type"] != "earnings") | (df["decided_by"] == "manual")].copy()
review["opening"] = review["opening"].str[:200]
review.sort_values(["ticker", "filing_date"]).to_csv(
    PROCESSED / "classification_review.csv", index=False)
print("\nNon-earnings and manual decisions saved to data/processed/classification_review.csv")

# 6. Gap check: rule-rejected filings in quarters with no earnings release (possible misses)
is_earnings = df["release_type"] == "earnings"
covered = set(zip(df.loc[is_earnings, "ticker"], df.loc[is_earnings, "quarter"]))
in_covered = pd.Series([(t, q) in covered for t, q in zip(df["ticker"], df["quarter"])],
                       index=df.index)
gaps = df[~is_earnings & ~in_covered & (df["decided_by"] == "rule")]

print(f"\nGap check: {len(gaps)} rejected filings in quarters without an earnings release")
if len(gaps):
    print(gaps.assign(opening=gaps["opening"].str[:110])
              [["ticker", "filing_date", "score", "opening"]].to_string(index=False))