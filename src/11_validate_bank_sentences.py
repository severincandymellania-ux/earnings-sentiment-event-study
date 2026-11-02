"""
11_validate_bank_sentences.py
Phase 3, step 3a: FinBERT's accuracy on 100 hand-labelled bank sentences from this dataset.
  1. Writes two label columns to data/labels/bank_sentences_to_label.csv:
     label_first_pass (my blind labels) and label_final (agreed after review)
  2. Compares FinBERT's answer (the label with the highest probability) with label_final,
     overall and separately for cost and credit-loss sentences
"""
import sqlite3

import pandas as pd

from config import PROCESSED, PROJECT_ROOT

LABELS_FILE = PROJECT_ROOT / "data" / "labels" / "bank_sentences_to_label.csv"
CODES = {"p": "positive", "n": "negative", "o": "neutral"}

# Metrics where "down" is good news and "up" is bad news (same list as 09 and 10)
REVERSED = (r"expense|charge-off|charge off|provision|nonperforming|non-performing|"
            r"delinquen|credit loss|allowance")

# Blind first-pass labels, recorded before the review (10 per block, in file order)
FIRST_PASS = ("nnppnnnppp" "nnnnppnpnn" "npnpnnnppn" "ppppppnppn" "npppnnpppp"
              "ppnpppnppp" "nnpnppnppn" "pnnnpnpppp" "pnppnpnppn" "ppppnnnpnp")
# Final labels after review of disagreements (10 per block, in file order)
FINAL = ("noppponpnn" "nnonponppp" "nppppnopoo" "nnpppnnppp" "onpppnpnnn"
         "nnonnpnppp" "poppppoopo" "ppnoppoopp" "popnonnnnp" "ppppnnnnpp")

# 1. Write both label columns to the file
df = pd.read_csv(LABELS_FILE, encoding="utf-8-sig")
assert len(df) == 100 and len(FIRST_PASS) == 100 and len(FINAL) == 100, \
    "Expected 100 sentences, 100 first-pass labels and 100 final labels"
df = df.drop(columns=["label"], errors="ignore")          # replaced by the two columns below
df["label_first_pass"] = [CODES[c] for c in FIRST_PASS]
df["label_final"] = [CODES[c] for c in FINAL]
df.to_csv(LABELS_FILE, index=False, encoding="utf-8-sig")

# 2. FinBERT's scores for these sentences (already computed by 08_score_finbert.py)
con = sqlite3.connect(PROCESSED / "earnings.db")
scores = pd.read_sql("""
    SELECT accession_number, sentence_no, p_positive, p_negative, p_neutral
    FROM sentence_scores
""", con)
con.close()

df = df.merge(scores, on=["accession_number", "sentence_no"], how="left")
df["finbert"] = (df[["p_positive", "p_negative", "p_neutral"]]
                 .idxmax(axis=1).str.replace("p_", "", regex=False))
df["reversed_metric"] = df["text"].str.contains(REVERSED, case=False, regex=True)

# 3. Accuracy: overall and by group
def accuracy(d, column="finbert"):
    return (d[column] == d["label_final"]).mean()

rev, other = df[df["reversed_metric"]], df[~df["reversed_metric"]]
print("FinBERT accuracy against the final labels:")
print(f"  All sentences                   {accuracy(df):6.0%}   (n = {len(df)})")
print(f"  Cost and credit-loss sentences  {accuracy(rev):6.0%}   (n = {len(rev)})")
print(f"  Other sentences                 {accuracy(other):6.0%}   (n = {len(other)})")

# 4. Confusion matrices: rows = true label, columns = FinBERT's answer
for name, d in [("All sentences", df), ("Cost and credit-loss sentences", rev)]:
    print(f"\nConfusion matrix, {name} (rows = true label, columns = FinBERT):")
    print(pd.crosstab(d["label_final"], d["finbert"], margins=True, margins_name="total"))

# 5. Human first pass vs. final labels and vs. FinBERT
print("\nMy blind first-pass labels:")
print(f"  Agreement with final labels  all {accuracy(df, 'label_first_pass'):4.0%} | "
      f"cost and credit-loss {accuracy(rev, 'label_first_pass'):4.0%} | "
      f"other {accuracy(other, 'label_first_pass'):4.0%}")
print(f"  Agreement with FinBERT       all "
      f"{(df['label_first_pass'] == df['finbert']).mean():4.0%}")