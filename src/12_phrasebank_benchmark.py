"""
12_phrasebank_benchmark.py
Phase 3, step 3b: FinBERT on the Financial PhraseBank, the standard benchmark
(2,264 financial news sentences on which all expert annotators agreed).
Note: ProsusAI/finbert was trained on Financial PhraseBank data, so this is a best-case,
partly in-sample score; the hand-labelled bank test (step 3a) is the out-of-sample check.
Source: Malo et al. (2014), via huggingface.co/datasets/takala/financial_phrasebank
(licence CC BY-NC-SA 3.0)
Output: data/processed/phrasebank_predictions.csv
"""
import zipfile

import pandas as pd
from huggingface_hub import hf_hub_download
from transformers import pipeline

from config import PROCESSED

# Metrics where "down" is good news and "up" is bad news (same list as 09, 10 and 11)
REVERSED = (r"expense|charge-off|charge off|provision|nonperforming|non-performing|"
            r"delinquen|credit loss|allowance")

# 1. Download the PhraseBank (a zip file, cached by Hugging Face after the first run)
zip_path = hf_hub_download(repo_id="takala/financial_phrasebank",
                           filename="data/FinancialPhraseBank-v1.0.zip",
                           repo_type="dataset")
with zipfile.ZipFile(zip_path) as z:
    member = next(n for n in z.namelist() if n.endswith("Sentences_AllAgree.txt"))
    lines = z.read(member).decode("latin-1").splitlines()   # the file uses old Latin-1 encoding

# Each line looks like: "Operating profit rose to EUR 13.1 mn .@positive"
rows = [line.rsplit("@", 1) for line in lines if "@" in line]
pb = pd.DataFrame(rows, columns=["text", "label"])
pb["label"] = pb["label"].str.strip()
print(f"PhraseBank sentences (all annotators agree): {len(pb)}")
print(pb["label"].value_counts().to_string(), "\n")

# 2. Score every sentence with FinBERT
finbert = pipeline("text-classification", model="ProsusAI/finbert",
                   top_k=None, truncation=True)
print("Scoring with FinBERT, this takes about 5 to 10 minutes...")
results = finbert(pb["text"].tolist(), batch_size=32)
pb["finbert"] = [max(r, key=lambda s: s["score"])["label"] for r in results]
pb["reversed_metric"] = pb["text"].str.contains(REVERSED, case=False, regex=True)

# 3. Accuracy: overall, and on cost and credit-loss sentences vs. the rest
def accuracy(d):
    return (d["finbert"] == d["label"]).mean()

rev, other = pb[pb["reversed_metric"]], pb[~pb["reversed_metric"]]
print("\nFinBERT accuracy on the Financial PhraseBank:")
print(f"  All sentences                   {accuracy(pb):6.1%}   (n = {len(pb)})")
print(f"  Cost and credit-loss sentences  {accuracy(rev):6.1%}   (n = {len(rev)})")
print(f"  Other sentences                 {accuracy(other):6.1%}   (n = {len(other)})")

print("\nConfusion matrix (rows = expert label, columns = FinBERT):")
print(pd.crosstab(pb["label"], pb["finbert"], margins=True, margins_name="total"))

# 4. Save predictions, and show a few cost and credit-loss sentences
pb.to_csv(PROCESSED / "phrasebank_predictions.csv", index=False)
pd.set_option("display.max_colwidth", 120)
print("\nSome PhraseBank cost and credit-loss sentences:")
print(rev[["text", "label", "finbert"]].head(8).to_string(index=False))