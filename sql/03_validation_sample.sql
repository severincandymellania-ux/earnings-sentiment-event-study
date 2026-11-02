-- 03_validation_sample.sql
-- Random sample of 40 releases labelled 'earnings', read by hand to check the
-- classification (result: 40 of 40 correct).

SELECT f.ticker,
       f.filing_date,
       substr(p.headline, 1, 200) AS start_of_text
FROM filings f
JOIN press_releases p USING (accession_number)
WHERE f.release_type = 'earnings'
ORDER BY RANDOM()
LIMIT 40;