# Does Earnings Tone Move the Stock? Financial Sentiment and Event Study on US Financials

> **Status:** In progress. Phase 1 of 5: collecting earnings releases from SEC EDGAR.

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
1. **NLP quality:** How accurate is FinBERT on expert-labelled financial sentences, and does it
   beat a standard finance word list (Loughran-McDonald)?
2. **Signal:** Are more negative releases followed by lower abnormal returns?
3. **Timing:** Does it matter whether a release is filed before the market opens or after it closes?
4. **Business value:** Would a simple rule (avoid the most negative 20% of releases) have beaten
   holding every stock?

## Data at a Glance
| Item | Count |
|---|---|
| Companies | 40 |
| Item 2.02 filings found, 2015 to 2025 | 1,737 |
| Filings with a press release attached | 1,725 (99.3%) |
| Excluded: no press release attached | 12 |
| Separating quarterly earnings releases from other Item 2.02 filings | In progress |

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
| 1d. Download texts | Press release texts stored in a SQLite database | In progress |
| 1e. Classify releases | Keep quarterly earnings releases, drop presentations and updates | Planned |
| 2. Sentiment scoring | Clean text, split into 512-token chunks, score with FinBERT | Planned |
| 3. Validation | FinBERT vs. expert labels and vs. the word-list baseline | Planned |
| 4. Event study | Market-model abnormal returns, regression of returns on tone | Planned |
| 5. App | Streamlit app: pick a company, see each release, its tone and the price reaction | Planned |

## Data Notes
These findings came up while building the dataset, and each one shaped a design decision.

- **Finding the earnings releases:** EDGAR has no "earnings" category. An earnings release is an
  8-K report tagged Item 2.02 ("Results of Operations and Financial Condition"), with the press
  release attached as an exhibit (EX-99.1 in 97% of filings, otherwise EX-99 or EX-99.01). File
  names change every quarter, so the exhibit is located by its document type, not its name.
- **Filtering is essential:** JPMorgan alone files about 26,000 documents a year on EDGAR, mostly
  paperwork for structured investment products. Only 4 are earnings releases.
- **Item 2.02 is not only quarterly earnings:** companies also use it for conference presentations
  and business updates. A company that reported every quarter would have 44 filings in 11 years;
  PNC has 94, with extras in March, November and December around investor conferences, and
  Robinhood has 29 since listing in 2021 instead of about 18. Neither the 8-K items, the dates nor
  the exhibit descriptions separate them reliably (PNC and Robinhood leave descriptions empty), so
  releases are classified from their text.
- **Excluded filings:** 12 filings have no press release attached (the information sits in a short
  paragraph in the 8-K form itself). They fall outside the companies' usual earnings dates and
  appear to be preliminary figures or short updates, so they are excluded.
- **Ticker changes:** BNY Mellon now trades as BNY and Fiserv as FISV. Companies are matched to
  EDGAR through the SEC's official ticker file and checked by name.
- **Filing times:** the `acceptanceDateTime` field in the EDGAR submissions API is unreliable.
  Compared with the "Accepted" time on each filing's index page, it is off by 8 hours (1,128
  filings), 10 hours (423), 4 hours (134) or 5 hours (52). Only the 4 and 5 hour gaps match the
  real New York to UTC offset, so filing times are taken from the index page.
- **Filing before the open:** JPMorgan files its earnings 8-K before the market opens (between
  about 6:30 and 8:40 am New York time in 2026), so the market reaction starts on the filing date.

## Project Structure
```text
earnings-sentiment-event-study/
├── data/
│   ├── raw/                               untouched downloads from EDGAR (not on GitHub)
│   └── processed/                         cleaned tables and SQLite database (not on GitHub)
├── src/
│   ├── config.py                          shared settings and company list
│   ├── private_settings_example.py        template for your SEC contact email
│   ├── 01_explore_edgar.py                explores one company's EDGAR filings
│   ├── 02_collect_earnings_filings.py     finds all Item 2.02 8-Ks, 2015 to 2025
│   ├── 03_parse_filing_index.py           filing times and press release links
│   └── 04_download_press_releases.py      downloads press release texts into SQLite
├── sql/
│   └── 01_schema.sql                      database tables: filings, press_releases
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
```

**3. Add your email.** Copy `src/private_settings_example.py` to `src/private_settings.py` and put
your own email in it. The SEC requires a contact email with every request
([fair access rules](https://www.sec.gov/os/accessing-edgar-data)).

**4. Run the scripts in order**
```bash
python src/02_collect_earnings_filings.py    # about 1 to 3 minutes
python src/03_parse_filing_index.py          # about 10 to 20 minutes
python src/04_download_press_releases.py     # about 15 to 25 minutes
```
Every download is cached in `data/raw/`, so if a run stops, rerunning continues where it left off.
`01_explore_edgar.py` is an exploration step and is not needed to reproduce the data.

## Author
**Candy Mellania Severin**, MSc Business Analytics and Data Science (UMCS Lublin; Erasmus+ at JKU Linz)