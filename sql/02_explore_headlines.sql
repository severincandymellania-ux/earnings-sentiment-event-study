-- 02_explore_headlines.sql
-- Exploration queries behind the earnings-release classification rule (Phase 1e).
-- Run in DB Browser for SQLite on data/processed/earnings.db

-- 1. How many releases mention "quarter"? (1,598 of 1,725)
SELECT COUNT(*)                       AS total_releases,
       SUM(headline LIKE '%quarter%') AS mention_quarter
FROM press_releases;

-- 2. Releases WITHOUT "quarter": many are real releases written as "Q4-15", "1Q23", "Full Year"
SELECT f.ticker,
       f.filing_date,
       substr(p.headline, 1, 250) AS start_of_text
FROM filings f
JOIN press_releases p USING (accession_number)
WHERE p.headline NOT LIKE '%quarter%'
ORDER BY f.ticker, f.filing_date;

-- 3. Releases WITH "quarter" that look like extras: catches Robinhood order routing reports,
--    but also real releases that mention a "conference call"
SELECT f.ticker,
       f.filing_date,
       substr(p.headline, 1, 250) AS start_of_text
FROM filings f
JOIN press_releases p USING (accession_number)
WHERE p.headline LIKE '%quarter%'
  AND (p.headline LIKE '%conference%'
       OR p.headline LIKE '%presentation%'
       OR p.headline LIKE '%order routing%')
ORDER BY f.ticker, f.filing_date;