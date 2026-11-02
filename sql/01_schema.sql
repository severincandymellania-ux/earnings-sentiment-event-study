-- 01_schema.sql
-- Database structure for the earnings sentiment project (SQLite).

-- One row per earnings 8-K filing
CREATE TABLE IF NOT EXISTS filings (
    accession_number  TEXT PRIMARY KEY,   -- EDGAR's unique filing ID
    ticker            TEXT NOT NULL,
    company           TEXT,
    segment           TEXT,
    cik               TEXT,
    filing_date       TEXT,               -- YYYY-MM-DD
    accepted_ny       TEXT,               -- YYYY-MM-DD HH:MM:SS, New York time
    items             TEXT,               -- 8-K items, e.g. "2.02,9.01"
    exhibit_type      TEXT,               -- EX-99.1, EX-99 or EX-99.01
    exhibit_url       TEXT,
    release_type      TEXT                -- earnings, other or no_text (set by 05_classify_releases.py)
);

-- One row per downloaded press release
CREATE TABLE IF NOT EXISTS press_releases (
    accession_number  TEXT PRIMARY KEY REFERENCES filings(accession_number),
    headline          TEXT,               -- first 60 words, used to classify releases
    n_words           INTEGER,
    full_text         TEXT
);

-- One row per clean narrative sentence of an earnings release (built by 07_clean_texts.py)
CREATE TABLE IF NOT EXISTS sentences (
    accession_number  TEXT REFERENCES filings(accession_number),
    sentence_no       INTEGER,            -- position in the release, starting at 0
    text              TEXT,
    n_words           INTEGER,
    PRIMARY KEY (accession_number, sentence_no)
);

-- FinBERT probabilities for each clean sentence (built by 08_score_finbert.py)
CREATE TABLE IF NOT EXISTS sentence_scores (
    accession_number  TEXT,
    sentence_no       INTEGER,
    p_positive        REAL,               -- probabilities add up to 1
    p_negative        REAL,
    p_neutral         REAL,
    PRIMARY KEY (accession_number, sentence_no),
    FOREIGN KEY (accession_number, sentence_no) REFERENCES sentences(accession_number, sentence_no)
);