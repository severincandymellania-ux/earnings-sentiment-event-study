"""
10_release_tone.py
Phase 2, step 2d: one tone score per earnings release.
  Sentence tone = P(positive) - P(negative), from -1 (very negative) to +1 (very positive)
  tone_all   = average tone over all sentences of the release
  tone_clean = average tone over sentences that do NOT mention costs or credit-loss
               metrics, where FinBERT reads the direction backwards (see README)
Stores the result in the release_tone table of data/processed/earnings.db
"""
import sqlite3

import pandas as pd

from config import PROCESSED

pd.set_option("display.width", 200)

# Metrics where "down" is good news and "up" is bad news (same list as 09_make_label_sample.py)
REVERSED = (r"expense|charge-off|charge off|provision|nonperforming|non-performing|"
            r"delinquen|credit loss|allowance")

con = sqlite3.connect(PROCESSED / "earnings.db")

# 1. Every scored sentence with its tone and its release's details
df = pd.read_sql("""
    SELECT f.accession_number, f.ticker, f.segment, f.filing_date,
           s.text,
           sc.p_positive - sc.p_negative AS tone
    FROM sentence_scores sc
    JOIN sentences s USING (accession_number, sentence_no)
    JOIN filings f USING (accession_number)
""", con)
df["reversed"] = df["text"].str.contains(REVERSED, case=False, regex=True)

# 2. Average per release: all sentences, and without reversed-metric sentences
tone_all = (df.groupby(["accession_number", "ticker", "segment", "filing_date"])
              .agg(tone_all=("tone", "mean"), n_sentences=("tone", "size"))
              .reset_index())
tone_clean = (df[~df["reversed"]].groupby("accession_number")
                .agg(tone_clean=("tone", "mean"), n_clean=("tone", "size"))
                .reset_index())
tone = tone_all.merge(tone_clean, on="accession_number", how="left")

# 3. Save as a table (rebuilt from scratch on every run)
tone.to_sql("release_tone", con, if_exists="replace", index=False)
con.close()

# 4. Checks
print(f"Releases with a tone score: {len(tone)}\n")
print(tone[["tone_all", "tone_clean"]].describe().round(3).to_string())
print(f"\nCorrelation between tone_all and tone_clean: "
      f"{tone['tone_all'].corr(tone['tone_clean']):.2f}")

# Average tone by filing quarter: does it drop in crises?
tone["quarter"] = pd.to_datetime(tone["filing_date"]).dt.to_period("Q").astype(str)
by_quarter = tone.groupby("quarter")[["tone_all", "tone_clean"]].mean().round(3)
by_quarter["gap"] = (by_quarter["tone_all"] - by_quarter["tone_clean"]).round(3)
print("\nAverage tone by filing quarter (gap = tone_all minus tone_clean):")
print(by_quarter.to_string())

cols = ["ticker", "filing_date", "tone_all", "tone_clean", "n_clean"]
print("\nFive most negative releases (tone_clean):")
print(tone.nsmallest(5, "tone_clean")[cols].round(3).to_string(index=False))
print("\nFive most positive releases (tone_clean):")
print(tone.nlargest(5, "tone_clean")[cols].round(3).to_string(index=False))