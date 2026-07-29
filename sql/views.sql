-- Analytics views consumed by Power BI and operational review.
CREATE OR REPLACE VIEW site_intelligence.v_candidate_decision AS
SELECT
    c.candidate_id,
    c.candidate_name,
    s.location_rank,
    s.location_score,
    s.predicted_sales_try_m,
    s.accessible_pop_drive_10,
    s.accessible_pop_walk_15,
    s.cannibalization_risk,
    s.opening_cost_try_m,
    s.roi_3y,
    s.recommendation_tier,
    c.delivery_risk,
    c.permitting_months,
    ST_Y(c.geom) AS latitude,
    ST_X(c.geom) AS longitude,
    ST_AsText(c.geom) AS geometry_wkt
FROM site_intelligence.candidate_site c
JOIN site_intelligence.candidate_score s USING (candidate_id);

CREATE OR REPLACE VIEW site_intelligence.v_competition_proximity AS
SELECT
    c.candidate_id,
    COUNT(r.competitor_id) FILTER (
        WHERE ST_DWithin(c.geom::geography, r.geom::geography, 3000)
    ) AS competitors_within_3km,
    MIN(ST_Distance(c.geom::geography, r.geom::geography)) / 1000.0 AS nearest_competitor_km
FROM site_intelligence.candidate_site c
CROSS JOIN site_intelligence.competitor r
GROUP BY c.candidate_id;

CREATE OR REPLACE VIEW site_intelligence.v_candidate_poi_mix AS
SELECT
    c.candidate_id,
    p.category,
    COUNT(*) AS poi_count_2km,
    AVG(p.attraction_index) AS average_attraction
FROM site_intelligence.candidate_site c
JOIN site_intelligence.poi p
  ON ST_DWithin(c.geom::geography, p.geom::geography, 2000)
GROUP BY c.candidate_id, p.category;

CREATE OR REPLACE VIEW site_intelligence.v_white_space_summary AS
SELECT
    CASE
        WHEN white_space_index >= 75 THEN 'High'
        WHEN white_space_index >= 50 THEN 'Medium'
        ELSE 'Low'
    END AS opportunity_band,
    COUNT(*) AS microzone_count,
    SUM(population) AS population,
    AVG(purchasing_power_index) AS purchasing_power_index,
    AVG(rent_try_sqm_month) AS rent_try_sqm_month
FROM site_intelligence.h3_microzone
WHERE NOT existing_covered
GROUP BY 1;

