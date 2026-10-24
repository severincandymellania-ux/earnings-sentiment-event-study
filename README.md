# Does Earnings Tone Move the Stock? Financial Sentiment and Event Study on US Financials

> **Status:** In progress. Phase 1 of 5: collecting earnings releases from SEC EDGAR.

## Business Problem
Investors and risk teams read hundreds of earnings releases each quarter. This project reads them
automatically, scores their tone with FinBERT (a financial language model), and tests whether tone
predicts how the stock moves over the following 1, 3 and 5 trading days, compared with the market.

**Scope:** about 40 large US banks, payment companies and fintechs (JPMorgan, Goldman Sachs, Citi,
Bank of America, PayPal, Visa, Mastercard and peers), 2015 to 2025.

## Business Questions
1. **NLP quality:** How accurate is FinBERT on expert-labelled financial sentences, and does it
   beat a standard finance word list (Loughran-McDonald)?
2. **Signal:** Are more negative releases followed by lower abnormal returns?
3. **Timing:** Does it matter whether a release is filed before the market opens or after it closes?
4. **Business value:** Would a simple rule (avoid the most negative 20% of releases) have beaten
   holding every stock?

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
| 1. Data collection | Find every earnings 8-K per company on EDGAR, download Exhibit 99.1, store text and filing time in SQLite | In progress |
| 2. Sentiment scoring | Clean text, split into 512-token chunks, score with FinBERT | Planned |
| 3. Validation | FinBERT vs. expert labels and vs. the word-list baseline | Planned |
| 4. Event study | Market-model abnormal returns, regression of returns on tone | Planned |
| 5. App | Streamlit app: pick a company, see each release, its tone and the price reaction | Planned |

## Data Notes
- **Finding the earnings releases:** EDGAR has no "earnings" category. An earnings release is an
  8-K report tagged Item 2.02 ("Results of Operations and Financial Condition"), with the press
  release attached as Exhibit 99.1. File names change every quarter, so the exhibit is located by
  its document type (EX-99.1), not its name. Exhibit 99.2 (the financial supplement, mostly
  number tables) is not used.
- **Filtering is essential:** JPMorgan alone files about 26,000 documents a year on EDGAR, mostly
  paperwork for structured investment products. Only 4 are earnings releases.
- **Filing times:** the `acceptanceDateTime` field in the EDGAR submissions API does not match the
  "Accepted" time on the filing's index page (for example 14:30:38 vs. 06:30:38 New York time for
  JPMorgan's Q3 2026 release). Filing times are therefore taken from the index page.
- **JPMorgan files before the market opens** (between about 6:30 and 8:40 am New York time in
  2026), so the market reaction starts on the filing date itself.

## Project Structure
```text
earnings-sentiment-event-study/
├── data/
│   ├── raw/                   untouched downloads from EDGAR (not on GitHub)
│   └── processed/             cleaned data and SQLite database (not on GitHub)
├── src/
│   └── 01_explore_edgar.py    explores one company's EDGAR filings
├── sql/                       SQL queries
├── notebooks/                 exploration notebooks
├── figures/                   charts used in this README
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

**3. Add your name and email** to the `User-Agent` line in the scripts. The SEC requires it
and blocks requests without it ([fair access rules](https://www.sec.gov/os/accessing-edgar-data)).

**4. Run the scripts in order**
```bash
python src/01_explore_edgar.py
```

*More steps are added as each phase is completed.*