#!/usr/bin/env python3
"""
Simplified ML Training Pipeline - Phase 3
Uses scikit-learn only for initial implementation
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
import json
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Add data collection agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection_v2'))

from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from context_data_agent import ContextDataAgent

class SimplifiedMLPipeline:
    """Simplified ML pipeline using scikit-learn"""
    
    def __init__(self):
        self.agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent(),
            'context': ContextDataAgent()
        }
        self.models = {}
        self.scalers = {}
        
    def collect_team_data(self, team_name: str) -> Dict[str, float]:
        """Collect numerical data for a team"""
        team_data = {}
        
        try:
            # Collect from all agents
            for agent_name, agent in self.agents.items():
                result = agent.execute_collection(team_name, "Premier League")
                if result:
                    for key, value in result['data'].items():
                        if isinstance(value, (int, float)):
                            team_data[f"{agent_name}_{key}"] = float(value)
            
            # Add mock squad data if missing
            if not any('squad' in key for key in team_data.keys()):
                team_data.update({
                    'squad_total_squad_value': np.random.uniform(100, 1500),
                    'squad_squad_depth_index': np.random.uniform(30, 90),
                    'squad_starting_xi_avg_value': np.random.uniform(20, 120)
                })
            
            return team_data
            
        except Exception as e:
            print(f"⚠️ Error collecting data for {team_name}: {e}")
            return {}
    
    def create_training_data(self, teams: List[str], num_samples: int = 25) -> pd.DataFrame:
        """Create training dataset from team combinations"""
        print(f"🔄 Creating training data from {len(teams)} teams...")
        
        training_data = []
        
        # Get data for all teams first
        team_data_cache = {}
        for team in teams:
            team_data_cache[team] = self.collect_team_data(team)
            if team_data_cache[team]:
                print(f"   ✅ {team}: {len(team_data_cache[team])} parameters")
            else:
                print(f"   ❌ {team}: Failed to collect data")
        
        # Create match combinations
        valid_teams = [team for team, data in team_data_cache.items() if data]
        
        for i, home_team in enumerate(valid_teams):
            for j, away_team in enumerate(valid_teams):
                if i != j and len(training_data) < num_samples:
                    
                    home_data = team_data_cache[home_team]
                    away_data = team_data_cache[away_team]
                    
                    # Create match features
                    match_features = self._create_match_features(home_data, away_data)
                    match_features['home_team'] = home_team
                    match_features['away_team'] = away_team
                    
                    # Simulate outcome (in production, use real historical results)
                    outcome = self._simulate_outcome(home_data, away_data)
                    match_features.update(outcome)
                    
                    training_data.append(match_features)
        
        print(f"✅ Created {len(training_data)} training samples")
        return pd.DataFrame(training_data)
    
    def _create_match_features(self, home_data: Dict[str, float], away_data: Dict[str, float]) -> Dict[str, float]:
        """Create features for ML model"""
        features = {}
        
        # Get common parameters
        common_params = set(home_data.keys()).intersection(set(away_data.keys()))
        
        for param in common_params:
            if 'team_name' not in param:
                home_val = home_data[param]
                away_val = away_data[param]
                
                # Create differential and absolute features
                features[f"diff_{param}"] = home_val - away_val
                features[f"home_{param}"] = home_val
                features[f"away_{param}"] = away_val
                features[f"ratio_{param}"] = home_val / (away_val + 0.1)  # Avoid division by zero
        
        return features
    
    def _simulate_outcome(self, home_data: Dict[str, float], away_data: Dict[str, float]) -> Dict[str, Any]:
        """Simulate match outcome with realistic variety"""
        
        # Use random values to ensure variety in training data
        # In production, this would be replaced with real historical results
        
        # Simulate goals with realistic distributions
        home_goals = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.15, 0.25, 0.25, 0.20, 0.10, 0.05])
        away_goals = np.random.choice([0, 1, 2, 3, 4], p=[0.20, 0.30, 0.25, 0.15, 0.10])
        
        # Determine result
        if home_goals > away_goals:
            result = 'H'
        elif away_goals > home_goals:
            result = 'A'
        else:
            result = 'D'
        
        # Ensure some variety in outcomes by forcing different results for different matches
        match_id = hash(str(home_data.get('elo_standard_elo', 0)) + str(away_data.get('elo_standard_elo', 0))) % 3
        if match_id == 0 and np.random.random() > 0.7:
            result = 'H'
            home_goals = max(home_goals, away_goals + 1)
        elif match_id == 1 and np.random.random() > 0.7:
            result = 'A'
            away_goals = max(away_goals, home_goals + 1)
        elif match_id == 2 and np.random.random() > 0.8:
            result = 'D'
            away_goals = home_goals
        
        total_goals = home_goals + away_goals
        
        return {
            'result': result,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'total_goals': total_goals,
            'over_2_5': 1 if total_goals > 2.5 else 0,
            'over_1_5': 1 if total_goals > 1.5 else 0,
            'btts': 1 if home_goals > 0 and away_goals > 0 else 0
        }
    
    def train_models(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Train all ML models"""
        print("🧠 Training ML Models...")
        
        # Prepare features
        feature_cols = [col for col in df.columns if col not in [
            'home_team', 'away_team', 'result', 'home_goals', 'away_goals',
            'total_goals', 'over_2_5', 'over_1_5', 'btts'
        ]]
        
        X = df[feature_cols].fillna(0)
        
        results = {}
        
        # 1. Match Outcome Model
        print("   🏆 Training Match Outcome Model...")
        y_result = df['result']
        
        # Encode labels
        le_result = LabelEncoder()
        y_result_encoded = le_result.fit_transform(y_result)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y_result_encoded, test_size=0.2, random_state=42)
        
        # Scale features
        scaler_result = StandardScaler()
        X_train_scaled = scaler_result.fit_transform(X_train)
        X_test_scaled = scaler_result.transform(X_test)
        
        # Train model
        rf_result = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
        rf_result.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = rf_result.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"      ✅ Match Outcome Accuracy: {accuracy:.3f}")
        
        self.models['match_outcome'] = {
            'model': rf_result,
            'label_encoder': le_result,
            'feature_names': feature_cols
        }
        self.scalers['match_outcome'] = scaler_result
        results['match_outcome'] = {'accuracy': accuracy}
        
        # 2. Goals Model
        print("   ⚽ Training Goals Model...")
        y_goals = df['total_goals']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y_goals, test_size=0.2, random_state=42)
        
        # Scale features
        scaler_goals = StandardScaler()
        X_train_scaled = scaler_goals.fit_transform(X_train)
        X_test_scaled = scaler_goals.transform(X_test)
        
        # Train model
        rf_goals = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
        rf_goals.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = rf_goals.predict(X_test_scaled)
        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        
        print(f"      ✅ Goals Model R²: {r2:.3f}, MSE: {mse:.3f}")
        
        self.models['goals'] = {
            'model': rf_goals,
            'feature_names': feature_cols
        }
        self.scalers['goals'] = scaler_goals
        results['goals'] = {'r2': r2, 'mse': mse}
        
        # 3. Over/Under Models
        for market in ['over_2_5', 'over_1_5', 'btts']:
            print(f"   📈 Training {market} Model...")
            
            y_market = df[market]
            X_train, X_test, y_train, y_test = train_test_split(X, y_market, test_size=0.2, random_state=42)
            
            # Scale features
            scaler_market = StandardScaler()
            X_train_scaled = scaler_market.fit_transform(X_train)
            X_test_scaled = scaler_market.transform(X_test)
            
            # Train model
            lr_market = LogisticRegression(random_state=42, max_iter=1000)
            lr_market.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = lr_market.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"      ✅ {market} Accuracy: {accuracy:.3f}")
            
            self.models[market] = {
                'model': lr_market,
                'feature_names': feature_cols
            }
            self.scalers[market] = scaler_market
            results[market] = {'accuracy': accuracy}
        
        return results
    
    def predict_match(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Make predictions for a specific match"""
        
        # Collect team data
        home_data = self.collect_team_data(home_team)
        away_data = self.collect_team_data(away_team)
        
        if not home_data or not away_data:
            return {'error': 'Could not collect team data'}
        
        # Create features
        features = self._create_match_features(home_data, away_data)
        
        # Convert to DataFrame
        feature_df = pd.DataFrame([features])
        
        predictions = {
            'home_team': home_team,
            'away_team': away_team,
            'prediction_timestamp': datetime.now().isoformat()
        }
        
        # Make predictions with each model
        for model_name, model_info in self.models.items():
            try:
                # Get feature columns for this model
                model_features = model_info['feature_names']
                X = feature_df[model_features].fillna(0)
                
                # Scale features
                X_scaled = self.scalers[model_name].transform(X)
                
                # Make prediction
                model = model_info['model']
                
                if model_name == 'match_outcome':
                    # Predict probabilities
                    proba = model.predict_proba(X_scaled)[0]
                    labels = model_info['label_encoder'].classes_
                    
                    predictions[model_name] = {
                        labels[i]: float(proba[i]) for i in range(len(labels))
                    }
                    
                elif model_name == 'goals':
                    # Predict total goals
                    pred_goals = model.predict(X_scaled)[0]
                    predictions[model_name] = {
                        'predicted_goals': float(pred_goals)
                    }
                    
                else:
                    # Binary classification (over/under, btts)
                    proba = model.predict_proba(X_scaled)[0]
                    predictions[model_name] = {
                        'probability': float(proba[1]),  # Probability of positive class
                        'prediction': bool(proba[1] > 0.5)
                    }
                    
            except Exception as e:
                predictions[model_name] = {'error': str(e)}
        
        return predictions
    
    def save_models(self, save_dir: str = "models/ml_simple"):
        """Save all models and scalers"""
        os.makedirs(save_dir, exist_ok=True)
        
        # Save models
        models_path = os.path.join(save_dir, "models.pkl")
        with open(models_path, 'wb') as f:
            pickle.dump(self.models, f)
        
        # Save scalers
        scalers_path = os.path.join(save_dir, "scalers.pkl")
        with open(scalers_path, 'wb') as f:
            pickle.dump(self.scalers, f)
        
        print(f"💾 Saved models to {save_dir}")

def main():
    """Test the Simplified ML Pipeline"""
    print("🧠 SIMPLIFIED ML TRAINING PIPELINE")
    print("="*60)
    
    # Initialize pipeline
    ml_pipeline = SimplifiedMLPipeline()
    
    # Test teams
    test_teams = [
        "Manchester City", "Real Madrid", "Inter", "Bayern München", 
        "Arsenal", "Barcelona", "Liverpool", "Chelsea"
    ]
    
    # Create training data
    print("🔄 Step 1: Creating Training Data")
    training_df = ml_pipeline.create_training_data(test_teams, num_samples=20)
    
    if len(training_df) == 0:
        print("❌ No training data created")
        return
    
    print(f"📊 Training dataset: {training_df.shape}")
    
    # Train models
    print("🔄 Step 2: Training Models")
    results = ml_pipeline.train_models(training_df)
    
    # Save models
    print("🔄 Step 3: Saving Models")
    ml_pipeline.save_models()
    
    # Test prediction
    print("🔄 Step 4: Testing Prediction")
    prediction = ml_pipeline.predict_match("Manchester City", "Real Madrid")
    
    print(f"\n🎯 SAMPLE PREDICTION: Manchester City vs Real Madrid")
    print("="*50)
    
    if 'match_outcome' in prediction:
        outcome = prediction['match_outcome']
        print(f"Match Outcome: {outcome}")
    
    if 'goals' in prediction:
        goals = prediction['goals']
        print(f"Expected Goals: {goals['predicted_goals']:.1f}")
    
    if 'over_2_5' in prediction:
        over25 = prediction['over_2_5']
        print(f"Over 2.5 Goals: {over25['probability']:.1%}")
    
    # Summary
    print(f"\n📋 ML PIPELINE SUMMARY")
    print("="*40)
    print(f"✅ Models Trained: {len(results)}")
    for model_name, metrics in results.items():
        if 'accuracy' in metrics:
            print(f"   {model_name}: {metrics['accuracy']:.3f} accuracy")
        elif 'r2' in metrics:
            print(f"   {model_name}: {metrics['r2']:.3f} R² score")
    
    print(f"\n🚀 Phase 3 ML Foundation Ready!")

if __name__ == "__main__":
    main()