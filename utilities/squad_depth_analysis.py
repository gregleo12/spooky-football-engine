#!/usr/bin/env python3
"""
Squad Depth Analysis Tool
Comprehensive analysis of squad depth utility for team strength calculations
"""
import sqlite3
import json
import statistics
from collections import defaultdict

def correlation(x, y):
    """Calculate Pearson correlation coefficient"""
    n = len(x)
    if n == 0:
        return 0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = sum((x[i] - mean_x)**2 for i in range(n))
    den_y = sum((y[i] - mean_y)**2 for i in range(n))
    
    den = (den_x * den_y)**0.5
    return num / den if den != 0 else 0

def analyze_squad_depth_data():
    """Analyze current squad depth implementation"""
    print("🔍 SQUAD DEPTH ANALYSIS REPORT")
    print("=" * 60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get all club teams data
    c.execute("""
        SELECT 
            cts.team_name,
            c.name as league,
            cts.squad_depth_score,
            cts.overall_strength,
            cts.elo_score,
            cts.squad_value_score,
            cts.form_score
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        AND cts.squad_depth_score IS NOT NULL
        AND cts.overall_strength IS NOT NULL
        ORDER BY cts.squad_depth_score DESC
    """)
    
    data = c.fetchall()
    
    # Extract data for analysis
    teams = [row[0] for row in data]
    leagues = [row[1] for row in data]
    depth_scores = [row[2] for row in data]
    overall_strengths = [row[3] for row in data]
    elo_scores = [row[4] for row in data]
    squad_values = [row[5] for row in data]
    form_scores = [row[6] for row in data]
    
    print(f"\n📊 DATA OVERVIEW")
    print(f"Total teams analyzed: {len(data)}")
    print(f"Squad depth range: {min(depth_scores):.4f} - {max(depth_scores):.4f}")
    print(f"Squad depth std dev: {statistics.stdev(depth_scores):.4f}")
    print(f"Squad depth variance: {statistics.variance(depth_scores):.6f}")
    
    # Show extreme cases
    print(f"\n🔝 TOP 10 SQUAD DEPTH TEAMS:")
    print(f"{'Team':<20} {'League':<15} {'Depth':<8} {'Overall':<8} {'ELO':<6} {'Value':<8}")
    print("-" * 80)
    for i in range(min(10, len(data))):
        team, league, depth, overall, elo, value = data[i][:6]
        print(f"{team:<20} {league:<15} {depth:<8.3f} {overall:<8.2f} {elo:<6.0f} €{value:<7.0f}M")
    
    print(f"\n📉 BOTTOM 10 SQUAD DEPTH TEAMS:")
    print(f"{'Team':<20} {'League':<15} {'Depth':<8} {'Overall':<8} {'ELO':<6} {'Value':<8}")
    print("-" * 80)
    for i in range(len(data)-10, len(data)):
        if i >= 0:
            team, league, depth, overall, elo, value = data[i][:6]
            print(f"{team:<20} {league:<15} {depth:<8.3f} {overall:<8.2f} {elo:<6.0f} €{value:<7.0f}M")
    
    # Correlation analysis
    print(f"\n📈 CORRELATION ANALYSIS:")
    corr_depth_overall = correlation(depth_scores, overall_strengths)
    corr_depth_elo = correlation(depth_scores, elo_scores)
    corr_depth_value = correlation(depth_scores, squad_values)
    corr_depth_form = correlation(depth_scores, form_scores)
    
    print(f"Squad Depth vs Overall Strength: {corr_depth_overall:+.4f}")
    print(f"Squad Depth vs ELO Score:       {corr_depth_elo:+.4f}")
    print(f"Squad Depth vs Squad Value:     {corr_depth_value:+.4f}")
    print(f"Squad Depth vs Form Score:      {corr_depth_form:+.4f}")
    
    # For comparison - other metric correlations
    print(f"\n📊 BASELINE CORRELATIONS (for comparison):")
    corr_elo_overall = correlation(elo_scores, overall_strengths)
    corr_value_overall = correlation(squad_values, overall_strengths)
    corr_form_overall = correlation(form_scores, overall_strengths)
    
    print(f"ELO vs Overall Strength:        {corr_elo_overall:+.4f}")
    print(f"Squad Value vs Overall Strength: {corr_value_overall:+.4f}")
    print(f"Form vs Overall Strength:       {corr_form_overall:+.4f}")
    
    # League-specific analysis
    print(f"\n🏆 LEAGUE-SPECIFIC ANALYSIS:")
    league_stats = defaultdict(list)
    for i, league in enumerate(leagues):
        league_stats[league].append(depth_scores[i])
    
    for league, depths in league_stats.items():
        print(f"{league:<15}: {min(depths):.3f} - {max(depths):.3f} (range: {max(depths)-min(depths):.3f})")
    
    # Impact analysis
    print(f"\n⚡ CURRENT IMPACT ON STRENGTH CALCULATION:")
    print(f"Squad depth weight: 2% (0.02)")
    max_impact = (max(depth_scores) - min(depth_scores)) * 0.02
    avg_impact = statistics.stdev(depth_scores) * 0.02
    print(f"Maximum possible impact: {max_impact:.4f} points")
    print(f"Typical impact (1 std dev): ±{avg_impact:.4f} points")
    
    # Recommendations
    print(f"\n🎯 ANALYSIS SUMMARY:")
    if abs(corr_depth_overall) < 0.1:
        print("❌ Squad depth shows WEAK correlation with overall strength")
    elif abs(corr_depth_overall) < 0.3:
        print("⚠️  Squad depth shows MODERATE correlation with overall strength")
    else:
        print("✅ Squad depth shows STRONG correlation with overall strength")
    
    if max_impact < 0.1:
        print("❌ Squad depth has MINIMAL impact on final strength scores")
    elif max_impact < 0.5:
        print("⚠️  Squad depth has LIMITED impact on final strength scores")
    else:
        print("✅ Squad depth has MEANINGFUL impact on final strength scores")
    
    conn.close()
    return {
        'correlation_with_strength': corr_depth_overall,
        'max_impact': max_impact,
        'data_range': max(depth_scores) - min(depth_scores),
        'std_dev': statistics.stdev(depth_scores)
    }

def test_without_squad_depth():
    """Test strength calculations without squad depth component"""
    print(f"\n🧪 TESTING STRENGTH CALCULATION WITHOUT SQUAD DEPTH")
    print("=" * 60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get data for calculation
    c.execute("""
        SELECT 
            cts.team_name,
            cts.overall_strength,
            cts.elo_score,
            cts.squad_value_score,
            cts.form_score,
            cts.squad_depth_score,
            cts.h2h_performance,
            cts.scoring_patterns
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        AND cts.overall_strength IS NOT NULL
        ORDER BY cts.overall_strength DESC
    """)
    
    data = c.fetchall()
    
    print(f"📊 RECALCULATED STRENGTHS (without squad depth):")
    print(f"{'Team':<20} {'Current':<8} {'No Depth':<8} {'Diff':<7}")
    print("-" * 60)
    
    changes = []
    for row in data[:15]:  # Top 15 teams
        team, current, elo, value, form, depth, h2h, scoring = row
        
        # Current weights: ELO(18%) + Value(15%) + Form(5%) + Depth(2%) + H2H(4%) + Scoring(3%)
        # Recalculate without depth (2%), redistribute proportionally
        # New weights: ELO(18.37%) + Value(15.31%) + Form(5.10%) + H2H(4.08%) + Scoring(3.06%)
        
        no_depth = (
            (elo or 0) * 0.1837 +
            (value or 0) * 0.1531 +
            (form or 0) * 0.0510 +
            (h2h or 0) * 0.0408 +
            (scoring or 0) * 0.0306
        )
        
        diff = no_depth - current
        changes.append(abs(diff))
        
        print(f"{team:<20} {current:<8.2f} {no_depth:<8.2f} {diff:+7.3f}")
    
    avg_change = statistics.mean(changes)
    max_change = max(changes)
    
    print(f"\n📈 IMPACT ANALYSIS:")
    print(f"Average absolute change: {avg_change:.3f} points")
    print(f"Maximum absolute change: {max_change:.3f} points")
    print(f"Changes > 0.1 points: {sum(1 for c in changes if c > 0.1)}/{len(changes)} teams")
    
    if avg_change < 0.05:
        print("✅ Removing squad depth would have MINIMAL impact")
    elif avg_change < 0.1:
        print("⚠️  Removing squad depth would have SMALL impact")
    else:
        print("❌ Removing squad depth would have SIGNIFICANT impact")
    
    conn.close()
    return avg_change, max_change

def main():
    """Run complete squad depth analysis"""
    try:
        # Change to parent directory for database access
        import os
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        analysis_results = analyze_squad_depth_data()
        avg_change, max_change = test_without_squad_depth()
        
        print(f"\n🎯 FINAL RECOMMENDATIONS:")
        print("=" * 60)
        
        correlation = analysis_results['correlation_with_strength']
        max_impact = analysis_results['max_impact']
        
        if abs(correlation) < 0.1 and max_impact < 0.1:
            print("❌ RECOMMENDATION: REMOVE squad depth from calculations")
            print("   • Weak correlation with team strength")
            print("   • Minimal impact on final scores")
            print("   • Adds noise rather than signal")
        elif abs(correlation) < 0.2 and max_impact < 0.2:
            print("⚠️  RECOMMENDATION: REDUCE squad depth weight or improve calculation")
            print("   • Limited predictive value in current form")
            print("   • Consider better implementation or removal")
        else:
            print("✅ RECOMMENDATION: KEEP squad depth but improve implementation")
            print("   • Shows meaningful correlation")
            print("   • Has measurable impact on scores")
        
        print(f"\n💡 Alternative: Redistribute 2% weight to proven metrics:")
        print(f"   • ELO: 18% → 19% (+1%)")
        print(f"   • Squad Value: 15% → 16% (+1%)")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())