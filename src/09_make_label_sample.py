"""
09_make_label_sample.py
Phase 3 preparation: draw a random sample of 100 cleaned sentences for hand labelling,
50 about costs and credit losses ("reversed" metrics) and 50 about everything else.
FinBERT's scores and the group of each sentence are deliberately left out, so the
labelling is blind.
Output: data/labels/bank_sentences_to_label.csv
"""
import sqlite3

import pandas as pd

from config import PROCESSED, PROJECT_ROOT

# Metrics where "down" is good news and "up" is bad news
REVERSED = (r"expense|charge-off|charge off|provision|nonperforming|non-performing|"
            r"delinquen|credit loss|allowance")

OUT_DIR = PROJECT_ROOT / "data" / "labels"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "bank_sentences_to_label.csv"

# Never overwrite labels you may already have entered
if OUT_FILE.exists():
    raise SystemExit(f"{OUT_FILE.name} already exists. Delete it first to draw a new sample.")

con = sqlite3.connect(PROCESSED / "earnings.db")
sents = pd.read_sql("""
    SELECT s.accession_number, s.sentence_no, f.ticker, s.text
    FROM sentences s
    JOIN filings f USING (accession_number)
""", con)
con.close()

sents["reversed_metric"] = sents["text"].str.contains(REVERSED, case=False, regex=True)

sample = pd.concat([
    sents[sents["reversed_metric"]].sample(50, random_state=42),
    sents[~sents["reversed_metric"]].sample(50, random_state=42),
]).sample(frac=1, random_state=42)          # shuffle, so the two groups are mixed

sample["label"] = ""                         # you fill this in: positive, negative or neutral
sample[["accession_number", "sentence_no", "ticker", "text", "label"]].to_csv(
    OUT_FILE, index=False, encoding="utf-8-sig")
print(f"Saved {len(sample)} sentences to {OUT_FILE}")