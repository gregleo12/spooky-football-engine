# Claude Code Phase 1 Brief: Spooky Engine Data Architecture Rebuild

## 🎯 Phase 1 Mission: Foundation First

**Objective**: Rebuild the data collection layer to support the new 11-parameter system while preserving all existing functionality.

**Critical Success Factor**: 100% data coverage for all 126 teams with new parameter structure.

---

## 🏗️ **Architecture Change Overview**

### **Current System Issues**
- Mixed data collection within calculation logic
- Squad depth agent producing counterintuitive results  
- Limited to 47% parameter coverage
- Hard to modify weights or add new parameters

### **New Architecture Goal**
```
BEFORE: Data Collection → Calculation (Tightly Coupled)
AFTER:  Data Collection → Standardized Storage → Flexible Calculation
```

**Benefits**:
- ✅ Change calculation logic without touching data collection
- ✅ Add new parameters easily
- ✅ A/B test different formulas
- ✅ Better error handling and validation

---

## 📊 **New Parameter Structure (11 Total)**

### **Keep & Enhance (From Current System)**
1. **ELO Rating** (20%) - Enhance with recency weighting
2. **Form Analysis** (20%) - Expand from 5% to 20%, add opponent quality
3. **Squad Value** (15%) - Split into Starting XI + Depth  
4. **H2H Performance** (keep at 4%) - Enhance with tactical analysis

### **Add New Parameters**
5. **Offensive Rating** (5%) - Goals scoring capability
6. **Defensive Rating** (5%) - Goals prevention capability  
7. **Squad Depth Index** (10%) - Quality-weighted depth (fix current issues)
8. **Home Advantage** (8%) - Team-specific venue boost
9. **Motivation & Stakes** (7%) - League position impact
10. **Tactical Matchup** (5%) - Style vs style analysis
11. **Key Player Availability** (2%) - Injury/suspension impact

**Total: 100% (up from current 47%)**

---

## 🔧 **Phase 1 Specific Tasks**

### **Data Agent Rebuild**

#### **Task 1.1: Enhanced ELO Agent**
```python
# File: agents/data_collection/enhanced_elo_agent.py
# Replace: agents/team_strength/competition_elo_agent.py

def collect_elo_data(team_id, competition_id):
    """Collect both standard ELO and recent form ELO"""
    standard_elo = get_api_football_elo(team_id)
    recent_matches = get_last_10_matches(team_id)
    recent_elo = calculate_recent_form_elo(recent_matches)
    
    return {
        'standard_elo': standard_elo,
        'recent_elo': recent_elo,
        'elo_trend': calculate_trend(recent_matches),
        'last_updated': datetime.now()
    }
```

#### **Task 1.2: Advanced Form Agent**  
```python
# File: agents/data_collection/advanced_form_agent.py
# Replace: agents/team_strength/competition_form_agent.py

def collect_form_data(team_id, competition_id):
    """Enhanced form with opponent quality weighting"""
    last_10_matches = get_recent_matches(team_id, count=10)
    
    form_score = 0
    for i, match in enumerate(last_10_matches):
        time_weight = 1.0 - (i * 0.1)  # Recent matches weighted more
        opponent_strength = get_opponent_elo(match.opponent_id)
        opponent_weight = opponent_strength / 2000  # Normalize
        
        match_points = 3 if match.result == 'W' else 1 if match.result == 'D' else 0
        form_score += match_points * time_weight * opponent_weight
    
    return {
        'raw_form_score': form_score,
        'opponent_adjusted_form': form_score / 10,  # Normalize 0-3
        'form_trend': calculate_trend_direction(last_10_matches)
    }
```

#### **Task 1.3: Goals Data Agent (NEW)**
```python
# File: agents/data_collection/goals_data_agent.py

def collect_goals_data(team_id, competition_id):
    """Collect offensive/defensive ratings for over/under markets"""
    season_matches = get_season_matches(team_id, competition_id)
    
    goals_scored = sum(match.goals_for for match in season_matches)
    goals_conceded = sum(match.goals_against for match in season_matches)
    matches_played = len(season_matches)
    
    # Opponent-adjusted ratings
    offensive_rating = calculate_opponent_adjusted_scoring(season_matches)
    defensive_rating = calculate_opponent_adjusted_conceding(season_matches)
    
    return {
        'goals_per_game': goals_scored / matches_played,
        'goals_conceded_per_game': goals_conceded / matches_played,
        'offensive_rating': offensive_rating,
        'defensive_rating': defensive_rating,
        'clean_sheet_percentage': calculate_clean_sheet_rate(season_matches)
    }
```

#### **Task 1.4: Enhanced Squad Value Agent**
```python
# File: agents/data_collection/enhanced_squad_value_agent.py
# Replace: agents/team_strength/competition_squad_value_agent.py

def collect_squad_data(team_id):
    """Split squad value into starting XI and depth components"""
    full_squad = get_transfermarkt_squad_values(team_id)
    typical_xi = calculate_most_used_xi(team_id, last_n_matches=10)
    
    starting_xi_values = [player.value for player in typical_xi]
    bench_values = [player.value for player in full_squad if player not in typical_xi]
    
    # Quality-weighted depth (fix the broken squad depth calculation)
    depth_index = calculate_quality_weighted_depth(full_squad)
    
    return {
        'total_squad_value': sum(player.value for player in full_squad),
        'starting_xi_avg_value': sum(starting_xi_values) / len(starting_xi_values),
        'squad_depth_index': depth_index,
        'key_player_values': sorted(starting_xi_values, reverse=True)[:3]
    }

def calculate_quality_weighted_depth(squad):
    """Fix the counterintuitive depth calculation"""
    sorted_players = sorted(squad, key=lambda p: p.value, reverse=True)
    
    first_xi = sorted_players[:11]
    second_xi = sorted_players[11:22] if len(sorted_players) > 11 else []
    
    first_xi_avg = sum(p.value for p in first_xi) / len(first_xi)
    second_xi_avg = sum(p.value for p in second_xi) / len(second_xi) if second_xi else 0
    
    # Weighted depth: 60% first XI quality, 40% second XI quality
    depth_score = (first_xi_avg * 0.6) + (second_xi_avg * 0.4)
    return depth_score
```

### **Context & Validation**

#### **Task 2.1: Context Data Agent (NEW)**
```python
# File: agents/data_collection/context_data_agent.py

def collect_context_data(team_id, competition_id):
    """Collect home advantage, motivation, fatigue data"""
    
    # Home advantage calculation
    home_record = get_home_record(team_id, competition_id)
    away_record = get_away_record(team_id, competition_id)
    home_advantage = calculate_home_vs_away_differential(home_record, away_record)
    
    # League position and motivation
    current_standings = get_league_standings(competition_id)
    team_position = get_team_position(team_id, current_standings)
    motivation = calculate_motivation_factor(team_position, current_standings)
    
    # Fixture congestion
    recent_fixtures = get_fixtures_last_30_days(team_id)
    fixture_density = len(recent_fixtures) / 30
    
    return {
        'home_advantage': home_advantage,
        'current_league_position': team_position,
        'motivation_factor': motivation,
        'fixture_congestion': fixture_density,
        'days_since_last_match': calculate_days_since_last_match(team_id)
    }
```

#### **Task 2.2: Data Validation Framework**
```python
# File: utilities/data_validation.py

def validate_complete_coverage():
    """Ensure 100% data coverage for all teams"""
    teams = get_all_teams()
    missing_data = []
    
    for team in teams:
        for parameter in REQUIRED_PARAMETERS:
            if not has_recent_data(team.id, parameter):
                missing_data.append(f"{team.name} missing {parameter}")
    
    if missing_data:
        raise DataCoverageError(f"Missing data: {missing_data}")
    
    return True

def validate_data_quality():
    """Sanity check all collected data"""
    # Check for reasonable ranges
    # Validate cross-references
    # Flag outliers for review
```

---

## 🗃️ **Database Schema Updates**

### **Enhanced Parameter Storage**
```sql
-- Add metadata to existing team_parameters table
ALTER TABLE team_parameters ADD COLUMN parameter_category TEXT; -- 'performance'|'squad'|'context'
ALTER TABLE team_parameters ADD COLUMN data_source TEXT; -- 'api_football'|'transfermarkt'|'calculated'
ALTER TABLE team_parameters ADD COLUMN confidence_level REAL; -- 0-1 data quality score

-- New parameter types to add
INSERT INTO parameter_definitions VALUES 
    ('offensive_rating', 'performance', 'Goals scoring capability'),
    ('defensive_rating', 'performance', 'Goals prevention capability'),
    ('starting_xi_avg_value', 'squad', 'Average value of typical starting XI'),
    ('home_advantage', 'context', 'Team-specific home venue boost'),
    ('motivation_factor', 'context', 'League position motivation'),
    ('fixture_congestion', 'context', 'Recent match density');
```

---

## 🎯 **Phase 1 Success Criteria**

### **Data Coverage Requirements**
- ✅ All 126 teams have data for all 11 parameters
- ✅ No missing or null values for core parameters
- ✅ Data quality validation passes for all teams
- ✅ Update timestamps within last 7 days

### **Quality Validation**
- ✅ Squad depth calculation no longer shows Chelsea < Alaves
- ✅ Cross-league normalizations remain consistent  
- ✅ ELO and form data correlates logically
- ✅ All new parameters have reasonable value ranges

### **Performance Requirements**
- ✅ Data collection completes within 30 minutes for all teams
- ✅ Individual agent execution time < 2 minutes per team
- ✅ Database queries remain fast (<1 second)
- ✅ Memory usage stays within reasonable limits

---

## 🔍 **Testing & Validation Plan**

### **Unit Testing**
```python
# Test each agent individually
def test_enhanced_elo_agent():
    # Test with known team ID
    # Verify output format and ranges
    # Check error handling

def test_goals_data_agent():
    # Test offensive/defensive calculations
    # Verify clean sheet percentages
    # Check opponent adjustment logic
```

### **Integration Testing**
```python
def test_complete_data_pipeline():
    # Run all agents for sample team
    # Verify data flows to database correctly
    # Check normalization across competitions
    # Validate no data loss from current system
```

### **Regression Testing**
```python
def test_backward_compatibility():
    # Ensure existing Flask app still works
    # Verify current team rankings don't break dramatically
    # Check API endpoints remain functional
```

---

## 📋 **Deliverables for Phase 1**

### **Code Deliverables**
1. **5 New/Enhanced Data Agents** (fully tested)
2. **Data Validation Framework** (comprehensive checks)
3. **Database Schema Updates** (backward compatible)
4. **Updated Competition Normalizer** (handles new parameters)
5. **Test Suite** (unit + integration tests)

### **Documentation**
1. **Agent Documentation** (inputs, outputs, dependencies)
2. **Data Quality Report** (coverage and validation results)
3. **Performance Metrics** (execution times, memory usage)
4. **Migration Guide** (how new system differs from old)

### **Validation Reports**
1. **Data Coverage Report** (100% coverage verification)
2. **Quality Validation Report** (sanity checks passed)
3. **Performance Benchmark** (speed and resource usage)
4. **Regression Test Results** (existing functionality preserved)

---

## 🚀 **Next Steps After Phase 1**

Once Phase 1 is complete:
- **Phase 2**: Build the modular calculation engine
- **Phase 3**: Implement multi-market odds (match outcome, over/under, clean sheets)
- **Phase 4**: Enhanced web interface and API endpoints

**The foundation from Phase 1 will support all future enhancements while maintaining the core innovation of competition-aware normalization that makes cross-league comparisons possible.**

---

## ❓ **Questions for Clarification**

1. **Data Source Preferences**: Any specific preference for injury/availability data sources?
2. **Update Frequency**: Should data collection be automated daily or remain manual execution?
3. **Fallback Strategy**: How to handle when external APIs are unavailable?
4. **Testing Environment**: Any specific testing requirements or constraints?

**Focus for Phase 1: Get the data architecture right. Everything else builds on this foundation.**