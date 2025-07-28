#!/usr/bin/env python3
"""
Competition-aware normalization utilities for multi-league prediction system
Handles per-competition normalization of team strength metrics
"""
import sys
import os
from typing import Dict, List, Tuple, Optional

# Add project root to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_config import db_config

def normalize_metric_by_competition(
    competition_id: str, 
    metric_name: str,
    team_scores: Dict[str, float],
    conn
) -> Dict[str, float]:
    """
    Normalize a metric within a specific competition (0-1 scale)
    
    Args:
        competition_id: Competition UUID
        metric_name: Name of metric (e.g., 'elo_score', 'squad_value_score')
        team_scores: Dict of {team_id: raw_score}
        conn: Database connection
        
    Returns:
        Dict of {team_id: normalized_score}
    """
    if not team_scores:
        return {}
    
    raw_scores = list(team_scores.values())
    
    # Handle edge case: all teams have identical scores
    if len(set(raw_scores)) == 1:
        return {team_id: 0.5 for team_id in team_scores.keys()}
    
    min_score = min(raw_scores)
    max_score = max(raw_scores)
    score_range = max_score - min_score
    
    # Normalize each team's score within competition
    normalized_scores = {}
    for team_id, raw_score in team_scores.items():
        if score_range > 0:
            normalized = (raw_score - min_score) / score_range
        else:
            normalized = 0.5
        normalized_scores[team_id] = round(normalized, 3)
    
    return normalized_scores

def get_competition_teams(competition_id: str, conn) -> List[Tuple[str, str, int]]:
    """
    Get all teams participating in a competition
    
    Returns:
        List of (team_id, team_name, api_team_id) tuples
    """
    c = conn.cursor()
    c.execute("""
        SELECT cts.team_id, cts.team_name, t.api_team_id
        FROM competition_team_strength cts 
        JOIN teams t ON cts.team_id = t.id
        WHERE cts.competition_id = %s
    """, (competition_id,))
    
    return c.fetchall()

def update_competition_metric(
    competition_id: str,
    metric_column: str,
    normalized_column: str,
    team_scores: Dict[str, float],
    conn
) -> None:
    """
    Update both raw and normalized scores for a metric in competition_team_strength table
    
    Args:
        competition_id: Competition UUID
        metric_column: Raw metric column name (e.g., 'squad_depth_score')
        normalized_column: Normalized column name (e.g., 'squad_depth_normalized')
        team_scores: Dict of {team_id: raw_score}
        conn: Database connection
    """
    from datetime import datetime, timezone
    import uuid
    
    # Normalize scores within competition
    normalized_scores = normalize_metric_by_competition(
        competition_id, metric_column, team_scores, conn
    )
    
    c = conn.cursor()
    
    for team_id, raw_score in team_scores.items():
        normalized_score = normalized_scores.get(team_id, 0.5)
        
        # Get team name
        c.execute("SELECT name FROM teams WHERE id = %s", (team_id,))
        team_name_result = c.fetchone()
        team_name = team_name_result[0] if team_name_result else "Unknown"
        
        # Update existing record (teams already exist from population)
        c.execute(f"""
            UPDATE competition_team_strength 
            SET {metric_column} = %s, {normalized_column} = %s, last_updated = %s
            WHERE competition_id = %s AND team_id = %s AND season = %s
        """, (
            raw_score, normalized_score, datetime.now(timezone.utc),
            competition_id, team_id, "2024"
        ))

def get_competition_metric_summary(
    competition_id: str, 
    metric_column: str, 
    normalized_column: str,
    conn
) -> Dict:
    """
    Get summary statistics for a metric within a competition
    
    Returns:
        Dict with min, max, avg for both raw and normalized scores
    """
    c = conn.cursor()
    
    c.execute(f"""
        SELECT 
            MIN({metric_column}) as min_raw,
            MAX({metric_column}) as max_raw, 
            AVG({metric_column}) as avg_raw,
            MIN({normalized_column}) as min_norm,
            MAX({normalized_column}) as max_norm,
            AVG({normalized_column}) as avg_norm,
            COUNT(*) as team_count
        FROM competition_team_strength 
        WHERE competition_id = %s 
        AND {metric_column} IS NOT NULL
        AND {normalized_column} IS NOT NULL
    """, (competition_id,))
    
    result = c.fetchone()
    if not result or result[6] == 0:
        return {}
    
    return {
        "raw": {
            "min": round(result[0], 3) if result[0] else 0,
            "max": round(result[1], 3) if result[1] else 0,
            "avg": round(result[2], 3) if result[2] else 0
        },
        "normalized": {
            "min": round(result[3], 3) if result[3] else 0,
            "max": round(result[4], 3) if result[4] else 0, 
            "avg": round(result[5], 3) if result[5] else 0
        },
        "team_count": result[6]
    }

def list_competitions(conn) -> List[Tuple[str, str, str]]:
    """
    Get all available competitions
    
    Returns:
        List of (competition_id, name, type) tuples
    """
    c = conn.cursor()
    c.execute("SELECT id, name, type FROM competitions ORDER BY type, name")
    return c.fetchall()

def compare_cross_competition_scores(
    team_name: str, 
    metric_column: str,
    conn
) -> List[Tuple[str, float, float]]:
    """
    Compare a team's scores across different competitions
    
    Args:
        team_name: Team name to compare
        metric_column: Metric to compare (raw scores)
        
    Returns:
        List of (competition_name, raw_score, normalized_score) tuples
    """
    c = conn.cursor()
    
    c.execute(f"""
        SELECT 
            comp.name as competition_name,
            cts.{metric_column} as raw_score,
            cts.{metric_column.replace('_score', '_normalized')} as normalized_score
        FROM competition_team_strength cts
        JOIN competitions comp ON cts.competition_id = comp.id
        WHERE cts.team_name = %s
        AND cts.{metric_column} IS NOT NULL
        ORDER BY comp.type, comp.name
    """, (team_name,))
    
    return c.fetchall()

if __name__ == '__main__':
    # Test the normalization utilities
    conn = db_config.get_connection()
    
    # List all competitions
    competitions = list_competitions(conn)
    print("🏆 Available Competitions:")
    for comp_id, name, comp_type in competitions:
        print(f"   {name} ({comp_type})")
    
    # Test metric summary for Premier League
    pl_comp_id = next(comp_id for comp_id, name, _ in competitions if name == 'Premier League')
    
    summary = get_competition_metric_summary(
        pl_comp_id, "squad_depth_score", "squad_depth_normalized", conn
    )
    
    if summary:
        print(f"\n📊 Premier League Squad Depth Summary:")
        print(f"   Raw scores: {summary['raw']['min']} - {summary['raw']['max']} (avg: {summary['raw']['avg']})")
        print(f"   Normalized: {summary['normalized']['min']} - {summary['normalized']['max']} (avg: {summary['normalized']['avg']})")
        print(f"   Teams: {summary['team_count']}")
    
    conn.close()