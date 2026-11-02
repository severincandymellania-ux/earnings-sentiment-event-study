"""
08_score_finbert.py
Phase 2, step 2c: scoring every clean sentence with FinBERT and storing the
probabilities in the sentence_scores table of data/processed/earnings.db.
Works one release at a time and skips releases already scored, so it can be
stopped and restarted at any point without losing work.
"""
import sqlite3
import time

import pandas as pd
from transformers import pipeline

from config import PROCESSED, PROJECT_ROOT

DB_PATH = PROCESSED / "earnings.db"
BATCH_SIZE = 32          # sentences FinBERT processes together; faster than one by one

finbert = pipeline("text-classification", model="ProsusAI/finbert",
                   top_k=None, truncation=True)

con = sqlite3.connect(DB_PATH)
con.executescript((PROJECT_ROOT / "sql" / "01_schema.sql").read_text(encoding="utf-8"))

# 1. Releases that still need scoring
todo = pd.read_sql("""
    SELECT DISTINCT accession_number
    FROM sentences
    WHERE accession_number NOT IN (SELECT DISTINCT accession_number FROM sentence_scores)
""", con)["accession_number"].tolist()
n_left = con.execute("""
    SELECT COUNT(*)
    FROM sentences
    WHERE accession_number NOT IN (SELECT DISTINCT accession_number FROM sentence_scores)
""").fetchone()[0]
print(f"Releases to score: {len(todo)}   Sentences to score: {n_left:,}\n")

# 2. Score release by release, saving after each one
start, n_done = time.time(), 0
for i, acc in enumerate(todo, start=1):
    sents = pd.read_sql("""
        SELECT sentence_no, text
        FROM sentences
        WHERE accession_number = ?
        ORDER BY sentence_no
    """, con, params=(acc,))

    results = finbert(sents["text"].tolist(), batch_size=BATCH_SIZE)

    rows = []
    for no, scores in zip(sents["sentence_no"], results):
        p = {s["label"]: s["score"] for s in scores}
        rows.append((acc, int(no), p["positive"], p["negative"], p["neutral"]))
    con.executemany("INSERT OR REPLACE INTO sentence_scores VALUES (?, ?, ?, ?, ?)", rows)
    con.commit()

    n_done += len(rows)
    if i % 20 == 0 or i == len(todo):
        rate = n_done / (time.time() - start)            # sentences per second
        minutes_left = (n_left - n_done) / rate / 60
        print(f"{i:>5}/{len(todo)} releases | {rate:5.1f} sentences/s | "
              f"about {minutes_left:4.0f} min left")

con.close()
print("\nDone. All sentences scored.")