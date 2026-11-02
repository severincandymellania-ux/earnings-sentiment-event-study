"""
06_finbert_check.py
Phase 2, step 2a: checking that FinBERT loads and scores a few example sentences.
The first run downloads the model (~440 MB) to the Hugging Face cache on this computer;
later runs load it from there.
"""
from transformers import pipeline

# A "pipeline" bundles the tokenizer (text -> tokens) and the model (tokens -> scores)
finbert = pipeline("text-classification", model="ProsusAI/finbert", top_k=None)

examples = [
    "Net income rose 18% to a record $5.2 billion, driven by strong loan growth.",
    "The bank recorded a $2.1 billion charge for credit losses as unemployment rose.",
    "The board declared a quarterly dividend of $0.25 per share.",
]

for sentence in examples:
    scores = finbert([sentence])[0]          # all three labels with their probabilities
    probs = {s["label"]: s["score"] for s in scores}
    best = max(probs, key=probs.get)         # the label with the highest probability
    print(f"\n{sentence}")
    print(f"  -> {best.upper()}   positive {probs['positive']:.2f} | "
          f"negative {probs['negative']:.2f} | neutral {probs['neutral']:.2f}")