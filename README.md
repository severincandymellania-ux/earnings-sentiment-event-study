# Does Earnings Tone Move the Stock? Financial Sentiment and Event Study on US Financials

> **Status:** Ongoing. Phase 1 complete (1,619 earnings releases). Phase 2 in progress: FinBERT scoring of 89,330 sentences, with a systematic model bias on bank language identified and measured.

## Business Problem
Investors and risk teams read hundreds of earnings releases each quarter. This project reads them
automatically, scores their tone with FinBERT (a financial language model), and tests whether tone
predicts how the stock moves over the following 1, 3 and 5 trading days, compared with the market.

**Scope:** 40 large US banks, payment companies, fintechs and exchanges, 2015 to 2025.

| Segment | Companies |
|---|---|
| Large banks | JPMorgan, Bank of America, Citigroup, Wells Fargo, Goldman Sachs, Morgan Stanley |
| Regional banks | U.S. Bancorp, PNC, Truist, M&T, Fifth Third, KeyCorp, Regions, Huntington, Citizens |
| Custody and wealth | BNY, State Street, Northern Trust, Charles Schwab |
| Consumer credit | Capital One, American Express, Synchrony, Ally |
| Payments | Visa, Mastercard, PayPal, Fiserv, FIS, Global Payments, Block |
| Fintech | SoFi, Affirm, Upstart, Robinhood, Coinbase |
| Exchanges and data | ICE, CME, Nasdaq, S&P Global, Moody's |

## Business Questions
1. **NLP quality:** How accurate is FinBERT on expert-labelled financial sentences and on bank
   sentences from this dataset, and does it beat a standard finance word list (Loughran-McDonald)?
2. **Signal:** Are more negative releases followed by lower abnormal returns?
3. **Timing:** Does it matter whether a release is filed before the market opens or after it closes?
4. **Business value:** Would a simple rule (avoid the most negative 20% of releases) have beaten
   holding every stock?

## Key Findings So Far
- **FinBERT misreads bank language in a systematic way.** It learned "up = good, down = bad" from
  general financial news, but for costs and credit-loss metrics the direction is reversed.
  *"Provision for credit losses increased... driven by higher energy-related charge-offs"* is
  scored **positive (0.96)**, and *"record low net charge-offs... down 4 basis points"* is scored
  **negative (0.98)**.
- **The bias is large and uneven.** 23% of all sentences mention costs or credit-loss metrics:
  28.9% for large banks and 26.9% for regional banks, but only 11.9% for payment companies and
  12.2% for exchanges. Lenders are affected more than twice as much.
- **Consequence for the study:** two tone scores are computed per release, one over all sentences
  and a corrected one excluding cost and credit-loss sentences, and both are tested in the event
  study. Releases are compared with the same company's earlier releases, so wording that repeats
  every quarter cancels out.

## Data at a Glance
| Step | Count |
|---|---|
| Item 2.02 filings found, 2015 to 2025 | 1,737 |
| Excluded: no press release attached | 12 |
| Press releases downloaded | 1,725 |
| Excluded: no readable text (slides saved as images) | 7 |
| Excluded: not an earnings release (presentations, legal news, order routing reports, updates) | 99 |
| **Quarterly earnings releases in the final dataset** | **1,619** |
| Companies with a release in all 44 quarters | 26 of 40 |
| Labels decided by hand (documented in the code) | 4 |
| Classification accuracy on a random sample of 40 releases, checked by reading | 40 of 40 |
| **Performance-related sentences extracted for FinBERT** | **89,330** |
| Sentence filter precision on a random sample of 20, checked by reading | 16 of 20 |
| Sentences about costs or credit losses (affected by the FinBERT bias) | 20,634 (23%) |
| Bank sentences hand-labelled for model validation | 100 |

## Data Sources
| Source | Used for | Access |
|---|---|---|
| [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation) | Earnings releases (8-K, Item 2.02, Exhibit 99.1) and filing times | Free, requires a User-Agent with name and email |
| [FinBERT (ProsusAI)](https://huggingface.co/ProsusAI/finbert) | Financial sentiment model | Free |
| [Financial PhraseBank](https://huggingface.co/datasets/takala/financial_phrasebank) | Expert-labelled sentences to test FinBERT | Free |
| [Loughran-McDonald Dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/) | Word-list baseline | Free for academic use |
| [yfinance](https://github.com/ranaroussi/yfinance) | Daily stock and S&P 500 prices | Free, unofficial |

## Methodology
| Phase | What happens | Status |
|---|---|---|
| 1a. Explore EDGAR | Inspect one company (JPMorgan) by hand to understand the data | Done |
| 1b. Collect filings | Every 8-K with Item 2.02 for 40 companies, 2015 to 2025, including older archive pages | Done |
| 1c. Parse index pages | Reliable filing time and press release link for every filing | Done |
| 1d. Download texts | Press release texts stored in a SQLite database | Done |
| 1e. Classify releases | Earnings score plus "one release per company per quarter" rule, gap check, manual review | Done |
| 2a. FinBERT check | Install PyTorch and transformers, test FinBERT on example sentences | Done |
| 2b. Clean texts | Split releases into sentences, keep performance-related narrative | Done |
| 2c. Score sentences | FinBERT probabilities (positive, negative, neutral) for every sentence | In progress |
| 2d. Release tone | Average tone per release, with and without cost and credit-loss sentences | Next |
| 3. Validation | FinBERT vs. Financial PhraseBank, vs. 100 hand-labelled bank sentences, and vs. the word-list baseline | Planned |
| 4. Event study | Market-model abnormal returns, regression of returns on tone, robustness checks | Planned |
| 5. App (optional) | Streamlit viewer: pick a company, see each release, its tone and the price reaction | Decided after Phase 4 |

## How Earnings Releases Were Identified
Item 2.02 ("Results of Operations and Financial Condition") is used for more than quarterly
earnings. Companies also file conference slides, investor day presentations, legal settlements,
leadership changes and regulatory reports under it. PNC alone has 94 Item 2.02 filings in 11 years
instead of 44. Keyword filters failed in both directions during exploration (see
`sql/02_explore_headlines.sql`), so the final rule combines a text score with the structure of
corporate reporting:

1. **Earnings score.** Points for earnings language in the first 300 words ("Third Quarter",
   "Q4-15", "1Q23", "Full Year", "Reports ... Results", "Net Income", "Net Loss", "Diluted EPS",
   "To Our Shareholders"). Penalties for signs of another document in the first 60 words only
   ("Conference" but not "conference call", "Investor Day", "Annual Meeting", "Order Routing",
   "Settlement with", "Recast").
2. **One release per company per quarter.** Within each company and calendar quarter, only the
   highest-scoring filing is kept, if it scores at least 2.
3. **Gap check.** Every rejected filing in a quarter without an earnings release is listed for
   review. The final run has none.
4. **Manual decisions.** Four filings the rule could not settle were read and decided by hand,
   each with a written reason in `src/05_classify_releases.py`.

Lessons from building the rule:
- **Position matters more than the word.** "Settlement" or "Investor Day" in a headline signals
  another document, but real releases use the same words in passing (for example "settlement of
  certain state tax matters" or "payment settlement").
- **"Quarter" is not proof of earnings.** Robinhood files quarterly SEC Rule 606 order routing
  reports under Item 2.02, and they mention "3rd Quarter".
- **Companies write results differently:** "Third Quarter 2022 Results and Key Metrics" (Citigroup),
  "Q4-15" (Bank of America), "1Q23" (U.S. Bancorp), shareholder letters (Block, Affirm, Coinbase).

## Preparing Text for FinBERT
FinBERT was trained on single sentences, so releases are scored sentence by sentence and the
release tone is the average over its sentences. This also shows which sentences drive a score.

- **Cleaning:** the EDGAR file label is removed, text is split at sentence ends and bullet points,
  and only sentences of 8 to 80 words that are mostly letters (not number tables) are kept.
- **Inclusion rather than exclusion:** removing boilerplate pattern by pattern reached only 8 of 20
  narrative sentences in a random sample, because disclaimers, footnotes and definitions come in
  endless forms. Keeping only sentences with performance language (rose, fell, higher, lower,
  compared with, record, strong, weak...) raised this to 16 of 20. The word list covers both
  directions equally, so it does not push tone up or down.
- **Trade-off:** exchanges publish short, table-heavy releases, so 53 releases (mostly CME and ICE)
  have fewer than 10 sentences and noisier tone scores. Phase 4 includes a robustness check
  without them.

## Validation Design
- **Financial PhraseBank:** thousands of financial news sentences labelled by experts, the standard
  benchmark for FinBERT.
- **Hand-labelled bank test set:** 100 sentences drawn from this dataset, 50 about costs and credit
  losses and 50 about everything else, labelled blind (without seeing FinBERT's scores) and then
  reviewed by a second annotator, with disagreements discussed and resolved. This measures
  FinBERT's accuracy on the actual data of this study, separately for the metrics where the bias
  was found.

## Data Notes
- **Finding the press release:** the press release is attached as an exhibit (EX-99.1 in 97% of
  filings, otherwise EX-99 or EX-99.01). File names change every quarter, so the exhibit is
  located by its document type, not its name.
- **Filtering is essential:** JPMorgan alone files about 26,000 documents a year on EDGAR, mostly
  paperwork for structured investment products. Only 4 are earnings releases.
- **Filing times:** the `acceptanceDateTime` field in the EDGAR submissions API is unreliable.
  Compared with the "Accepted" time on each filing's index page, it is off by 8 hours (1,128
  filings), 10 hours (423), 4 hours (134) or 5 hours (52). Only the 4 and 5 hour gaps match the
  real New York to UTC offset, so filing times are taken from the index page.
- **Ticker changes:** BNY Mellon now trades as BNY and Fiserv as FISV. Companies are matched to
  EDGAR through the SEC's official ticker file and checked by name.
- **Coverage below 44 quarters** has known causes: listing dates (SoFi, Robinhood, Coinbase, Affirm
  and Upstart in 2020 and 2021, Block in late 2015, PayPal's separation from eBay in July 2015),
  and a few quarters where a company filed no Item 2.02 8-K at all (Citigroup, Huntington, Morgan
  Stanley, Schwab, KeyCorp, S&P Global, Northern Trust).
- **Release length varies widely**, from about 1,100 words (Capital One) to 15,000 (Fifth Third),
  because some exhibits include full financial tables.

## Project Structure
```text
earnings-sentiment-event-study/
├── data/
│   ├── raw/                               untouched downloads from EDGAR (not on GitHub)
│   ├── processed/                         SQLite database and tables (not on GitHub)
│   └── labels/
│       └── bank_sentences_to_label.csv    100 hand-labelled bank sentences
├── src/
│   ├── config.py                          shared settings and company list
│   ├── private_settings_example.py        template for your SEC contact email
│   ├── 01_explore_edgar.py                explores one company's EDGAR filings
│   ├── 02_collect_earnings_filings.py     finds all Item 2.02 8-Ks, 2015 to 2025
│   ├── 03_parse_filing_index.py           filing times and press release links
│   ├── 04_download_press_releases.py      downloads press release texts into SQLite
│   ├── 05_classify_releases.py            labels real earnings releases
│   ├── 06_finbert_check.py                tests FinBERT on example sentences
│   ├── 07_clean_texts.py                  splits releases into clean performance sentences
│   ├── 08_score_finbert.py                scores every sentence with FinBERT (resumable)
│   └── 09_make_label_sample.py            draws the blind sample for hand labelling
├── sql/
│   ├── 01_schema.sql                      database tables
│   ├── 02_explore_headlines.sql           exploration queries behind the classification rule
│   ├── 03_validation_sample.sql           random sample used to check the labels
│   └── 04_finbert_checks.sql              queries that revealed the FinBERT bias
├── notebooks/                             exploration notebooks
├── figures/                               charts used in this README
└── README.md
```

## How to Reproduce
**1. Clone the repository and create a virtual environment** (Python 3.10 or newer)
```bash
git clone https://github.com/severincandymellania-ux/earnings-sentiment-event-study.git
cd earnings-sentiment-event-study
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac / Linux
```

**2. Install the packages**
```bash
python -m pip install requests pandas beautifulsoup4 lxml
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers
```
The second line installs the CPU-only version of PyTorch (about 250 MB instead of 2.5 GB).

**3. Add your email.** Copy `src/private_settings_example.py` to `src/private_settings.py` and put
your own email in it. The SEC requires a contact email with every request
([fair access rules](https://www.sec.gov/os/accessing-edgar-data)).

**4. Run the scripts in order**
```bash
python src/02_collect_earnings_filings.py    # about 1 to 3 minutes
python src/03_parse_filing_index.py          # about 10 to 20 minutes
python src/04_download_press_releases.py     # about 15 to 25 minutes
python src/05_classify_releases.py           # a few seconds
python src/07_clean_texts.py                 # under a minute
python src/08_score_finbert.py               # about 3 to 4 hours on a laptop CPU, resumable
```
Every download is cached in `data/raw/` and FinBERT scores are saved release by release, so if a
run stops, rerunning continues where it left off. `01_explore_edgar.py` and `06_finbert_check.py`
are exploration steps and are not needed to reproduce the data.

## Skills Demonstrated
Python (requests, pandas, BeautifulSoup, regular expressions) · REST APIs and web data collection ·
SQL and SQLite (schema design, joins, aggregation, subqueries, data validation) · NLP with Hugging
Face Transformers and FinBERT · model evaluation and bias analysis · rule-based text classification ·
blind annotation and inter-annotator review · data quality checks · Git and GitHub

## Author
**Candy Mellania Severin**, MSc Business Analytics and Data Science (UMCS Lublin; Erasmus+ at JKU Linz)