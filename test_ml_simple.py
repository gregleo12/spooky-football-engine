#!/usr/bin/env python3
"""
Simple ML Demo - Phase 3
Quick demonstration of machine learning for football prediction
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, r2_score
import warnings
warnings.filterwarnings('ignore')

def create_demo_data():
    """Create demo training data for ML models"""
    print("📊 Creating demo training data...")
    
    # Simulate team strength features
    np.random.seed(42)
    n_matches = 100
    
    data = []
    for i in range(n_matches):
        # Team features (simplified)
        home_elo = np.random.normal(1550, 100)
        away_elo = np.random.normal(1550, 100)
        home_attack = np.random.uniform(1.0, 3.0)
        away_attack = np.random.uniform(1.0, 3.0)
        home_defense = np.random.uniform(0.5, 2.0)
        away_defense = np.random.uniform(0.5, 2.0)
        home_form = np.random.uniform(0, 3)
        away_form = np.random.uniform(0, 3)
        home_advantage = np.random.uniform(0.4, 0.8)
        
        # Create features
        elo_diff = home_elo - away_elo
        attack_diff = home_attack - away_attack
        defense_diff = away_defense - home_defense  # Lower defense is better
        form_diff = home_form - away_form
        
        # Simulate match outcome based on features
        home_strength = 0.5 + (elo_diff / 400) + (attack_diff * 0.1) + (defense_diff * 0.1) + (form_diff * 0.05) + (home_advantage - 0.6) * 0.5
        home_strength = max(0.1, min(0.9, home_strength))
        
        # Determine result
        rand = np.random.random()
        if rand < home_strength * 0.6:  # Home win
            result = 'H'
            home_goals = max(0, int(np.random.poisson(home_attack * 1.2)))
            away_goals = max(0, int(np.random.poisson(away_attack * 0.8)))
        elif rand > 1 - (1 - home_strength) * 0.6:  # Away win
            result = 'A'
            home_goals = max(0, int(np.random.poisson(home_attack * 0.8)))
            away_goals = max(0, int(np.random.poisson(away_attack * 1.2)))
        else:  # Draw
            result = 'D'
            home_goals = max(0, int(np.random.poisson(home_attack)))
            away_goals = max(0, int(np.random.poisson(away_attack)))
        
        total_goals = home_goals + away_goals
        
        data.append({
            'elo_diff': elo_diff,
            'attack_diff': attack_diff,
            'defense_diff': defense_diff,
            'form_diff': form_diff,
            'home_advantage': home_advantage,
            'home_elo': home_elo,
            'away_elo': away_elo,
            'result': result,
            'total_goals': total_goals,
            'over_2_5': 1 if total_goals > 2.5 else 0,
            'home_goals': home_goals,
            'away_goals': away_goals
        })
    
    return pd.DataFrame(data)

def train_ml_models():
    """Train simple ML models for football prediction"""
    print("🧠 SIMPLE ML DEMO FOR FOOTBALL PREDICTION")
    print("="*60)
    
    # Create training data
    df = create_demo_data()
    print(f"📊 Training data: {len(df)} matches")
    
    # Prepare features
    feature_cols = ['elo_diff', 'attack_diff', 'defense_diff', 'form_diff', 'home_advantage']
    X = df[feature_cols]
    
    print(f"🔢 Features: {feature_cols}")
    
    # 1. Match Outcome Model
    print("\n🏆 Training Match Outcome Model")
    
    y_result = df['result']
    X_train, X_test, y_train, y_test = train_test_split(X, y_result, test_size=0.2, random_state=42)
    
    # Scale features
    scaler_result = StandardScaler()
    X_train_scaled = scaler_result.fit_transform(X_train)
    X_test_scaled = scaler_result.transform(X_test)
    
    # Train model
    rf_result = RandomForestClassifier(n_estimators=50, random_state=42)
    rf_result.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = rf_result.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   ✅ Match Outcome Accuracy: {accuracy:.3f}")
    
    # Feature importance
    importance = dict(zip(feature_cols, rf_result.feature_importances_))
    print(f"   📊 Top features: {sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]}")
    
    # 2. Goals Model
    print("\n⚽ Training Total Goals Model")
    
    y_goals = df['total_goals']
    X_train, X_test, y_train, y_test = train_test_split(X, y_goals, test_size=0.2, random_state=42)
    
    # Scale features
    scaler_goals = StandardScaler()
    X_train_scaled = scaler_goals.fit_transform(X_train)
    X_test_scaled = scaler_goals.transform(X_test)
    
    # Train model
    rf_goals = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_goals.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = rf_goals.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    print(f"   ✅ Goals Model R² Score: {r2:.3f}")
    
    # 3. Over 2.5 Goals Model
    print("\n📈 Training Over 2.5 Goals Model")
    
    y_over25 = df['over_2_5']
    X_train, X_test, y_train, y_test = train_test_split(X, y_over25, test_size=0.2, random_state=42)
    
    # Scale features
    scaler_over25 = StandardScaler()
    X_train_scaled = scaler_over25.fit_transform(X_train)
    X_test_scaled = scaler_over25.transform(X_test)
    
    # Train model
    rf_over25 = RandomForestClassifier(n_estimators=50, random_state=42)
    rf_over25.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = rf_over25.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   ✅ Over 2.5 Goals Accuracy: {accuracy:.3f}")
    
    # Demo Prediction
    print("\n🎯 DEMO PREDICTION")
    print("="*40)
    
    # Example: Strong home team vs weaker away team
    demo_features = [[100, 0.5, 0.3, 0.4, 0.65]]  # elo_diff, attack_diff, defense_diff, form_diff, home_advantage
    
    # Scale features
    demo_scaled_result = scaler_result.transform(demo_features)
    demo_scaled_goals = scaler_goals.transform(demo_features)
    demo_scaled_over25 = scaler_over25.transform(demo_features)
    
    # Make predictions
    result_proba = rf_result.predict_proba(demo_scaled_result)[0]
    goals_pred = rf_goals.predict(demo_scaled_goals)[0]
    over25_proba = rf_over25.predict_proba(demo_scaled_over25)[0]
    
    print(f"Match: Strong Home Team vs Weaker Away Team")
    print(f"Features: ELO diff +100, Attack diff +0.5, Defense diff +0.3")
    print(f"")
    print(f"Predictions:")
    classes = rf_result.classes_
    for i, prob in enumerate(result_proba):
        print(f"   {classes[i]}: {prob:.1%}")
    print(f"   Expected Goals: {goals_pred:.1f}")
    print(f"   Over 2.5 Goals: {over25_proba[1]:.1%}")
    
    print(f"\n✅ ML Demo completed successfully!")
    print(f"🚀 Ready to integrate with real Spooky Engine data!")
    
    return {
        'result_model': rf_result,
        'goals_model': rf_goals,
        'over25_model': rf_over25,
        'scalers': {
            'result': scaler_result,
            'goals': scaler_goals,
            'over25': scaler_over25
        },
        'features': feature_cols
    }

if __name__ == "__main__":
    models = train_ml_models()