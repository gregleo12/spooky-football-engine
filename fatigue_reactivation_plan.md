# Fatigue Factor Reactivation Plan

## 🎯 Current Status
**Fatigue Factor temporarily deactivated** due to lack of discriminating fixture data (all teams = 0.5).

**Weight redistributed:**
- ELO Score: 20% → 21.5% (+1.5%)
- Form Score: 20% → 21.5% (+1.5%)  
- Fatigue Factor: 3% → 0% (temporarily inactive)

## 🔄 Reactivation Triggers

### **Automatic Reactivation Conditions:**
1. **Season starts** and regular fixtures begin
2. **API fixture data** shows variation between teams (not all 0.5)
3. **At least 50% of teams** have different fatigue scores

### **Manual Reactivation Steps:**

#### 1. Verify Data Quality
```bash
# Check if fatigue data is now meaningful
python3 -c "
import sqlite3
conn = sqlite3.connect('db/football_strength.db')
c = conn.cursor()
c.execute('SELECT COUNT(DISTINCT fatigue_factor) FROM competition_team_strength WHERE season = \"2024\"')
unique_values = c.fetchone()[0]
print(f'Unique fatigue values: {unique_values}')
if unique_values > 1:
    print('✅ Fatigue data is now discriminating - ready for reactivation')
else:
    print('❌ Still uniform data - keep current optimization')
"
```

#### 2. Revert Weight Distribution
Update `phase1_engine.py` weights:
```python
# Original weights (when fatigue data is available)
weights = {
    'elo_score': 0.20,                   # Back to 20%
    'squad_value_score': 0.15,           # Unchanged
    'form_score': 0.20,                  # Back to 20%
    'squad_depth_score': 0.10,           # Unchanged
    'offensive_rating': 0.05,            # Unchanged
    'defensive_rating': 0.05,            # Unchanged
    'home_advantage': 0.08,              # Unchanged
    'motivation_factor': 0.07,           # Unchanged
    'tactical_matchup': 0.05,            # Unchanged
    'fatigue_factor': 0.03,              # Reactivated to 3%
    'key_player_availability': 0.02      # Unchanged
}
```

#### 3. Update Fatigue Data
```bash
# Run fatigue factor agent with new data
python3 agents/team_strength/fatigue_factor_agent.py
```

#### 4. Recalculate Strength Scores
```bash
# Run main calculation engine with full 11 parameters
python3 phase1_engine.py
```

#### 5. Verification
```bash
# Verify all 11 parameters contributing
python3 phase1_verification_check.py
```

## 📊 Expected Impact of Reactivation

### **Current Optimized System:**
- ELO: 21.5% | Form: 21.5% | 8 other parameters: 57%
- 100% meaningful calculation
- Higher weight on most reliable parameters

### **Full 11-Parameter System:**
- ELO: 20% | Form: 20% | Fatigue: 3% | 8 other parameters: 57%
- More nuanced analysis including fixture congestion
- Better prediction accuracy for teams in multiple competitions

## ⚡ Alternative Data Sources (If Needed)

### **Historical Fixture Analysis:**
- Analyze previous season fixture patterns
- Use competition schedules to estimate congestion
- Apply fixture density calculations

### **Competition Calendar Integration:**
- European competition schedules
- Domestic cup fixtures
- International break periods

### **Manual Override System:**
- Allow manual fatigue adjustments for known situations
- Champion League weeks = higher fatigue
- Winter break periods = lower fatigue

## 🎯 Recommendation

**Keep current optimization until:**
1. Regular season fixtures resume
2. Fatigue agent shows discriminating values (not all 0.5)
3. System automatically detects meaningful fatigue variation

**This ensures 100% calculation value while maintaining system architecture for seamless reactivation.**

## 📅 Monitoring Schedule

**Weekly Check (during off-season):**
```bash
# Quick fatigue data check
python3 -c "
import sqlite3
conn = sqlite3.connect('db/football_strength.db')
c = conn.cursor()
c.execute('SELECT AVG(fatigue_factor), MIN(fatigue_factor), MAX(fatigue_factor) FROM competition_team_strength WHERE season = \"2024\"')
avg, min_val, max_val = c.fetchone()
print(f'Fatigue - Avg: {avg:.3f}, Range: {min_val:.3f}-{max_val:.3f}')
if max_val - min_val > 0.1:
    print('🔔 Fatigue data showing variation - consider reactivation')
"
```

**Monthly Review:**
- Check fixture data availability in API
- Review fatigue calculation logic
- Update reactivation timeline