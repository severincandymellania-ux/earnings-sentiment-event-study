-- 04_finbert_checks.sql
-- Queries that revealed FinBERT's bias on bank language (Phase 2).

-- 1. Most negative sentences: includes good news such as "record low net charge-offs"
SELECT s.text,
       ROUND(sc.p_negative, 2) AS negative,
       ROUND(sc.p_positive, 2) AS positive
FROM sentence_scores sc
JOIN sentences s USING (accession_number, sentence_no)
ORDER BY sc.p_negative DESC
LIMIT 15;

-- 2. Bad news phrased with "increased" is scored as positive
SELECT s.text,
       ROUND(sc.p_positive, 2) AS positive,
       ROUND(sc.p_negative, 2) AS negative
FROM sentence_scores sc
JOIN sentences s USING (accession_number, sentence_no)
WHERE s.text LIKE '%charge-offs increased%'
   OR s.text LIKE '%provision for credit losses increased%'
   OR s.text LIKE '%nonperforming%increased%'
LIMIT 15;

-- 3. How many sentences mention costs or credit-loss metrics? (20,634 of 89,330, 23%)
SELECT COUNT(*) AS all_sentences,
       SUM(text LIKE '%expense%'
           OR text LIKE '%charge-off%'
           OR text LIKE '%charge off%'
           OR text LIKE '%provision%'
           OR text LIKE '%nonperforming%'
           OR text LIKE '%non-performing%'
           OR text LIKE '%delinquen%'
           OR text LIKE '%credit loss%'
           OR text LIKE '%allowance%') AS reversed_metric_sentences
FROM sentences;

-- 4. Share of those sentences by segment (large banks 28.9%, payments 11.9%)
SELECT f.segment,
       COUNT(*) AS sentences,
       ROUND(100.0 * SUM(s.text LIKE '%expense%'
                         OR s.text LIKE '%charge-off%'
                         OR s.text LIKE '%charge off%'
                         OR s.text LIKE '%provision%'
                         OR s.text LIKE '%nonperforming%'
                         OR s.text LIKE '%non-performing%'
                         OR s.text LIKE '%delinquen%'
                         OR s.text LIKE '%credit loss%'
                         OR s.text LIKE '%allowance%') / COUNT(*), 1) AS pct_reversed
FROM sentences s
JOIN filings f USING (accession_number)
GROUP BY f.segment
ORDER BY pct_reversed DESC;