-- METABASE DASHBOARD QUERIES
-- Football Analytics System - Comprehensive Business Intelligence
-- Use these queries to create Metabase dashboards

-- =============================================================================
-- DASHBOARD 1: SYSTEM HEALTH OVERVIEW
-- =============================================================================

-- 1.1 System Health KPIs
-- Purpose: Monitor system data quality and coverage
SELECT 
    'Total Teams' as metric,
    COUNT(*) as value,
    'count' as format
FROM teams
UNION ALL
SELECT 
    'Strength Records' as metric,
    COUNT(*) as value,
    'count' as format
FROM competition_team_strength
UNION ALL
SELECT 
    'Competitions' as metric,
    COUNT(DISTINCT competition_id) as value,
    'count' as format
FROM competition_team_strength
UNION ALL
SELECT 
    'Data Coverage' as metric,
    ROUND((COUNT(*) * 100.0 / 98), 1) as value,
    'percentage' as format
FROM competition_team_strength 
WHERE elo_score IS NOT NULL;

-- 1.2 Parameter Coverage Analysis
-- Purpose: Track coverage percentage for each parameter
SELECT 
    'ELO Score' as parameter,
    COUNT(*) as covered,
    98 as total,
    ROUND((COUNT(*) * 100.0 / 98), 1) as coverage_percent
FROM competition_team_strength WHERE elo_score IS NOT NULL
UNION ALL
SELECT 
    'Squad Value' as parameter,
    COUNT(*) as covered,
    98 as total,
    ROUND((COUNT(*) * 100.0 / 98), 1) as coverage_percent
FROM competition_team_strength WHERE squad_value_score IS NOT NULL
UNION ALL
SELECT 
    'Form Score' as parameter,
    COUNT(*) as covered,
    98 as total,
    ROUND((COUNT(*) * 100.0 / 98), 1) as coverage_percent
FROM competition_team_strength WHERE form_score IS NOT NULL
UNION ALL
SELECT 
    'Squad Depth' as parameter,
    COUNT(*) as covered,
    98 as total,
    ROUND((COUNT(*) * 100.0 / 98), 1) as coverage_percent
FROM competition_team_strength WHERE squad_depth_score IS NOT NULL;

-- 1.3 Data Freshness Monitor
-- Purpose: Track when data was last updated
SELECT 
    c.name as competition,
    COUNT(*) as teams,
    MAX(cts.last_updated) as last_update,
    EXTRACT(epoch FROM (NOW() - MAX(cts.last_updated)))/3600 as hours_since_update
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
GROUP BY c.name
ORDER BY last_update DESC;

-- =============================================================================
-- DASHBOARD 2: FOOTBALL ANALYTICS INSIGHTS
-- =============================================================================

-- 2.1 Team Strength Rankings (Top 20)
-- Purpose: Display top teams across all competitions
SELECT 
    ROW_NUMBER() OVER (ORDER BY cts.elo_score DESC) as rank,
    cts.team_name,
    c.name as competition,
    cts.elo_score,
    cts.squad_value_score,
    cts.form_score,
    cts.overall_strength
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
ORDER BY cts.elo_score DESC
LIMIT 20;

-- 2.2 League Strength Comparison
-- Purpose: Compare average strength across leagues
SELECT 
    c.name as league,
    COUNT(*) as teams,
    ROUND(AVG(cts.elo_score), 1) as avg_elo,
    ROUND(AVG(cts.squad_value_score), 1) as avg_squad_value,
    ROUND(AVG(cts.overall_strength), 1) as avg_overall,
    ROUND(MIN(cts.elo_score), 1) as min_elo,
    ROUND(MAX(cts.elo_score), 1) as max_elo
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
GROUP BY c.name
ORDER BY avg_elo DESC;

-- 2.3 Parameter Correlation Analysis
-- Purpose: Show relationships between different metrics
SELECT 
    cts.team_name,
    c.name as league,
    cts.elo_score,
    cts.squad_value_score,
    cts.form_score,
    cts.squad_depth_score,
    -- Correlation indicators
    CASE 
        WHEN cts.elo_score > 1600 AND cts.squad_value_score > 80 THEN 'Elite'
        WHEN cts.elo_score > 1550 AND cts.squad_value_score > 60 THEN 'Strong'
        WHEN cts.elo_score > 1450 THEN 'Average'
        ELSE 'Developing'
    END as tier
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
ORDER BY cts.elo_score DESC;

-- 2.4 Competition Depth Analysis
-- Purpose: Analyze competitive balance within leagues
SELECT 
    c.name as league,
    COUNT(*) as total_teams,
    ROUND(MAX(cts.elo_score) - MIN(cts.elo_score), 1) as elo_range,
    ROUND(STDDEV(cts.elo_score), 1) as elo_stddev,
    -- Competitiveness indicator
    CASE 
        WHEN STDDEV(cts.elo_score) < 80 THEN 'Very Competitive'
        WHEN STDDEV(cts.elo_score) < 100 THEN 'Competitive'
        WHEN STDDEV(cts.elo_score) < 120 THEN 'Moderate'
        ELSE 'Top Heavy'
    END as competitiveness
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
GROUP BY c.name
ORDER BY elo_stddev ASC;

-- =============================================================================
-- DASHBOARD 3: PERFORMANCE MONITORING
-- =============================================================================

-- 3.1 Value Distribution Analysis
-- Purpose: Monitor data quality and outliers
SELECT 
    'ELO Score' as metric,
    ROUND(MIN(elo_score), 1) as min_value,
    ROUND(MAX(elo_score), 1) as max_value,
    ROUND(AVG(elo_score), 1) as avg_value,
    ROUND(STDDEV(elo_score), 1) as std_dev
FROM competition_team_strength
UNION ALL
SELECT 
    'Squad Value' as metric,
    ROUND(MIN(squad_value_score), 1) as min_value,
    ROUND(MAX(squad_value_score), 1) as max_value,
    ROUND(AVG(squad_value_score), 1) as avg_value,
    ROUND(STDDEV(squad_value_score), 1) as std_dev
FROM competition_team_strength
UNION ALL
SELECT 
    'Form Score' as metric,
    ROUND(MIN(form_score), 1) as min_value,
    ROUND(MAX(form_score), 1) as max_value,
    ROUND(AVG(form_score), 1) as avg_value,
    ROUND(STDDEV(form_score), 1) as std_dev
FROM competition_team_strength;

-- 3.2 Data Quality Indicators
-- Purpose: Monitor for missing data or anomalies
SELECT 
    'Complete Records' as check_type,
    COUNT(*) as count,
    'Should be 98' as expected
FROM competition_team_strength 
WHERE elo_score IS NOT NULL 
  AND squad_value_score IS NOT NULL 
  AND form_score IS NOT NULL
UNION ALL
SELECT 
    'ELO Range Check' as check_type,
    COUNT(*) as count,
    'Should be 0' as expected
FROM competition_team_strength 
WHERE elo_score < 1300 OR elo_score > 1700
UNION ALL
SELECT 
    'Value Range Check' as check_type,
    COUNT(*) as count,
    'Should be 0' as expected
FROM competition_team_strength 
WHERE squad_value_score < 0 OR squad_value_score > 100;

-- 3.3 Team Performance Trends
-- Purpose: Identify high/low performers for further analysis
SELECT 
    'Top Performers' as category,
    COUNT(*) as teams,
    'ELO > 1600' as criteria
FROM competition_team_strength 
WHERE elo_score > 1600
UNION ALL
SELECT 
    'Strong Teams' as category,
    COUNT(*) as teams,
    'ELO 1500-1600' as criteria
FROM competition_team_strength 
WHERE elo_score BETWEEN 1500 AND 1600
UNION ALL
SELECT 
    'Average Teams' as category,
    COUNT(*) as teams,
    'ELO 1400-1500' as criteria
FROM competition_team_strength 
WHERE elo_score BETWEEN 1400 AND 1500
UNION ALL
SELECT 
    'Developing Teams' as category,
    COUNT(*) as teams,
    'ELO < 1400' as criteria
FROM competition_team_strength 
WHERE elo_score < 1400;

-- =============================================================================
-- DASHBOARD 4: DETAILED ANALYTICS (ADVANCED)
-- =============================================================================

-- 4.1 Multi-Parameter Team Analysis
-- Purpose: Comprehensive team profiling
SELECT 
    cts.team_name,
    c.name as league,
    cts.elo_score,
    cts.squad_value_score,
    cts.form_score,
    cts.squad_depth_score,
    cts.key_player_availability_score,
    cts.motivation_factor_score,
    cts.offensive_rating,
    cts.defensive_rating,
    cts.overall_strength,
    -- Performance categories
    CASE 
        WHEN cts.offensive_rating > cts.defensive_rating THEN 'Attack Focused'
        WHEN cts.defensive_rating > cts.offensive_rating THEN 'Defense Focused'
        ELSE 'Balanced'
    END as play_style
FROM competition_team_strength cts
JOIN competitions c ON cts.competition_id = c.id
ORDER BY cts.overall_strength DESC;

-- 4.2 League Comparison Matrix
-- Purpose: Cross-league strength analysis
WITH league_stats AS (
    SELECT 
        c.name as league,
        AVG(cts.elo_score) as avg_elo,
        AVG(cts.squad_value_score) as avg_value,
        AVG(cts.overall_strength) as avg_overall,
        COUNT(*) as team_count
    FROM competition_team_strength cts
    JOIN competitions c ON cts.competition_id = c.id
    GROUP BY c.name
)
SELECT 
    league,
    team_count,
    ROUND(avg_elo, 1) as avg_elo,
    ROUND(avg_value, 1) as avg_squad_value,
    ROUND(avg_overall, 1) as avg_overall_strength,
    RANK() OVER (ORDER BY avg_elo DESC) as elo_rank,
    RANK() OVER (ORDER BY avg_value DESC) as value_rank,
    RANK() OVER (ORDER BY avg_overall DESC) as overall_rank
FROM league_stats
ORDER BY avg_overall DESC;

-- =============================================================================
-- CUSTOM FILTERS AND PARAMETERS
-- =============================================================================

-- These queries support Metabase filters and parameters:
-- {{league}} - Filter by competition name
-- {{min_elo}} - Minimum ELO score filter
-- {{team_name}} - Specific team filter

-- Example: Parameterized Team Search
-- SELECT * FROM competition_team_strength cts
-- JOIN competitions c ON cts.competition_id = c.id
-- WHERE cts.team_name ILIKE '%{{team_name}}%'
-- AND cts.elo_score >= {{min_elo}}
-- AND c.name = {{league}};