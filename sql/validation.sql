-- Post-load validation queries. Every result should return zero rows or a true flag.
SELECT candidate_id, COUNT(*)
FROM site_intelligence.candidate_site
GROUP BY candidate_id
HAVING COUNT(*) > 1;

SELECT h3_cell
FROM site_intelligence.h3_microzone
WHERE NOT ST_IsValid(geom) OR ST_SRID(geom) <> 4326;

SELECT
    COUNT(*) = COUNT(DISTINCT candidate_id) AS candidate_ids_unique,
    COUNT(*) FILTER (WHERE geom IS NULL) = 0 AS candidate_geometry_complete
FROM site_intelligence.candidate_site;

SELECT
    COUNT(*) FILTER (WHERE location_score NOT BETWEEN 0 AND 100) AS invalid_scores,
    COUNT(*) FILTER (WHERE cannibalization_risk NOT BETWEEN 0 AND 1) AS invalid_risks
FROM site_intelligence.candidate_score;

