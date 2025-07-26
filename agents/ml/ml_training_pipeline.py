#!/usr/bin/env python3
"""
Machine Learning Training Pipeline - Phase 3
Converts Phase 2 collected data into trained prediction models
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import json
import pickle
import sqlite3
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Add data collection agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection_v2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'calculation'))

from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from context_data_agent import ContextDataAgent

class MLDataPreprocessor:
    """Preprocesses Phase 2 data for machine learning"""
    
    def __init__(self, db_path: str = "db/football_strength.db"):
        self.db_path = db_path
        self.agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent(),
            'context': ContextDataAgent()
        }
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
    def collect_training_data(self, teams: List[str], num_samples: int = 50) -> pd.DataFrame:
        """
        Collect training data by simulating historical matches
        
        Args:
            teams: List of team names to use
            num_samples: Number of match samples to generate
            
        Returns:
            DataFrame with features and target variables
        """
        print(f"🔄 Collecting training data for {len(teams)} teams...")
        
        training_data = []
        
        # Generate team vs team combinations
        for i, team1 in enumerate(teams):
            for j, team2 in enumerate(teams):
                if i != j:  # Don't match team against itself
                    
                    # Collect data for both teams
                    team1_data = self._collect_team_data(team1)
                    team2_data = self._collect_team_data(team2)
                    
                    if team1_data and team2_data:
                        # Create match features
                        match_features = self._create_match_features(team1_data, team2_data)
                        match_features['home_team'] = team1
                        match_features['away_team'] = team2
                        
                        # Simulate match outcome (for training)
                        outcome = self._simulate_match_outcome(team1_data, team2_data)
                        match_features.update(outcome)
                        
                        training_data.append(match_features)
                        
                        if len(training_data) >= num_samples:
                            break
                            
            if len(training_data) >= num_samples:
                break
        
        print(f"✅ Collected {len(training_data)} training samples")
        return pd.DataFrame(training_data)
    
    def _collect_team_data(self, team_name: str) -> Dict[str, Any]:
        """Collect all available data for a team"""
        team_data = {'team_name': team_name}
        
        try:
            # Collect from all agents
            for agent_name, agent in self.agents.items():
                result = agent.execute_collection(team_name, "Premier League")
                if result:
                    # Prefix parameters with agent name to avoid conflicts
                    for key, value in result['data'].items():
                        team_data[f"{agent_name}_{key}"] = value
            
            # Add mock squad data if missing
            if 'squad_total_squad_value' not in team_data:
                team_data.update({
                    'squad_total_squad_value': np.random.uniform(100, 1500),
                    'squad_squad_depth_index': np.random.uniform(30, 90),
                    'squad_starting_xi_avg_value': np.random.uniform(20, 120)
                })
            
            return team_data
            
        except Exception as e:
            print(f"⚠️ Error collecting data for {team_name}: {e}")
            return {}
    
    def _create_match_features(self, home_data: Dict[str, Any], away_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create match-level features from team data"""
        features = {}
        
        # Feature categories
        feature_mappings = {
            'elo': ['standard_elo', 'recent_form_elo'],
            'form': ['raw_form_score', 'opponent_adjusted_form', 'form_consistency'],
            'goals': ['goals_per_game', 'goals_conceded_per_game', 'opponent_adjusted_offensive'],
            'context': ['overall_home_advantage', 'motivation_factor', 'current_position'],
            'squad': ['total_squad_value', 'squad_depth_index', 'starting_xi_avg_value']
        }
        
        # Create differential features (home - away)
        for category, params in feature_mappings.items():
            for param in params:
                home_key = f"{category}_{param}"
                away_key = f"{category}_{param}"
                
                home_val = home_data.get(home_key, 0)
                away_val = away_data.get(away_key, 0)
                
                # Convert to numeric
                if isinstance(home_val, (int, float)) and isinstance(away_val, (int, float)):
                    features[f"diff_{param}"] = home_val - away_val
                    features[f"home_{param}"] = home_val
                    features[f"away_{param}"] = away_val
                    features[f"avg_{param}"] = (home_val + away_val) / 2
        
        # Add contextual features
        features['home_advantage'] = home_data.get('context_overall_home_advantage', 0.5)
        
        return features
    
    def _simulate_match_outcome(self, home_data: Dict[str, Any], away_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate match outcome based on team strengths
        This is for training data generation - in production we'd use real historical results
        """
        # Calculate relative strengths
        home_elo = home_data.get('elo_standard_elo', 1500)
        away_elo = away_data.get('elo_standard_elo', 1500)
        home_goals_pg = home_data.get('goals_goals_per_game', 1.5)
        away_goals_pg = away_data.get('goals_goals_per_game', 1.5)
        home_goals_conceded = home_data.get('goals_goals_conceded_per_game', 1.0)
        away_goals_conceded = away_data.get('goals_goals_conceded_per_game', 1.0)
        home_advantage = home_data.get('context_overall_home_advantage', 0.6)
        
        # Simulate match outcome with some randomness
        strength_diff = (home_elo - away_elo) / 100
        home_attack_strength = home_goals_pg / (away_goals_conceded + 0.1)
        away_attack_strength = away_goals_pg / (home_goals_conceded + 0.1)
        
        # Apply home advantage
        home_attack_strength *= (1 + home_advantage * 0.2)
        
        # Simulate goals with Poisson-like distribution
        home_goals = max(0, int(np.random.poisson(home_attack_strength * 1.5)))
        away_goals = max(0, int(np.random.poisson(away_attack_strength * 1.3)))
        
        # Determine outcome
        if home_goals > away_goals:
            result = 'H'  # Home win
        elif away_goals > home_goals:
            result = 'A'  # Away win
        else:
            result = 'D'  # Draw
        
        total_goals = home_goals + away_goals
        
        return {
            'home_goals': home_goals,
            'away_goals': away_goals,
            'total_goals': total_goals,
            'result': result,
            'over_2_5': 1 if total_goals > 2.5 else 0,
            'over_1_5': 1 if total_goals > 1.5 else 0,
            'btts': 1 if home_goals > 0 and away_goals > 0 else 0,
            'home_clean_sheet': 1 if away_goals == 0 else 0,
            'away_clean_sheet': 1 if home_goals == 0 else 0
        }

class MLModelTrainer:
    """Trains machine learning models for football prediction"""
    
    def __init__(self):
        self.models = {}
        self.feature_names = []
        self.model_metrics = {}
        
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
        """Prepare features and targets from training data"""
        
        # Define feature columns (exclude target variables and metadata)
        exclude_cols = [
            'home_team', 'away_team', 'home_goals', 'away_goals', 
            'total_goals', 'result', 'over_2_5', 'over_1_5', 
            'btts', 'home_clean_sheet', 'away_clean_sheet'
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Prepare features
        X = df[feature_cols].copy()
        
        # Handle missing values
        X = X.fillna(0)
        
        # Prepare targets
        targets = {
            'match_result': df['result'],
            'total_goals': df['total_goals'],
            'over_2_5': df['over_2_5'],
            'over_1_5': df['over_1_5'],
            'btts': df['btts'],
            'home_clean_sheet': df['home_clean_sheet']
        }
        
        self.feature_names = feature_cols
        print(f"📊 Prepared {len(feature_cols)} features for training")
        
        return X, targets
    
    def train_match_outcome_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train model for match outcome prediction (H/D/A)"""
        print("🏆 Training Match Outcome Model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train XGBoost model
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss'
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        
        print(f"   ✅ Test Accuracy: {accuracy:.3f}")
        print(f"   ✅ CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Store model
        model_info = {
            'model': model,
            'scaler': scaler,
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': dict(zip(self.feature_names, model.feature_importances_))
        }
        
        self.models['match_outcome'] = model_info
        return model_info
    
    def train_goals_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train model for total goals prediction"""
        print("⚽ Training Goals Prediction Model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train XGBoost regressor
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"   ✅ MSE: {mse:.3f}")
        print(f"   ✅ R² Score: {r2:.3f}")
        
        # Store model
        model_info = {
            'model': model,
            'scaler': scaler,
            'mse': mse,
            'r2': r2,
            'feature_importance': dict(zip(self.feature_names, model.feature_importances_))
        }
        
        self.models['total_goals'] = model_info
        return model_info
    
    def train_market_models(self, X: pd.DataFrame, targets: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Train models for specific betting markets"""
        print("🎯 Training Market-Specific Models...")
        
        market_models = {}
        
        markets = ['over_2_5', 'over_1_5', 'btts', 'home_clean_sheet']
        
        for market in markets:
            if market in targets:
                print(f"   📈 Training {market} model...")
                
                y = targets[market]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                print(f"      ✅ {market} Accuracy: {accuracy:.3f}")
                
                market_models[market] = {
                    'model': model,
                    'scaler': scaler,
                    'accuracy': accuracy,
                    'feature_importance': dict(zip(self.feature_names, model.feature_importances_))
                }
        
        self.models.update(market_models)
        return market_models
    
    def save_models(self, save_dir: str = "models/ml"):
        """Save trained models to disk"""
        os.makedirs(save_dir, exist_ok=True)
        
        for model_name, model_info in self.models.items():
            # Save model
            model_path = os.path.join(save_dir, f"{model_name}_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model_info, f)
            
            print(f"💾 Saved {model_name} model to {model_path}")
        
        # Save feature names
        feature_path = os.path.join(save_dir, "feature_names.json")
        with open(feature_path, 'w') as f:
            json.dump(self.feature_names, f)
        
        print(f"💾 Saved feature names to {feature_path}")
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of all trained models"""
        summary = {
            'total_models': len(self.models),
            'feature_count': len(self.feature_names),
            'models': {}
        }
        
        for model_name, model_info in self.models.items():
            if 'accuracy' in model_info:
                summary['models'][model_name] = {
                    'accuracy': model_info['accuracy'],
                    'type': 'classification'
                }
            elif 'r2' in model_info:
                summary['models'][model_name] = {
                    'r2_score': model_info['r2'],
                    'mse': model_info['mse'],
                    'type': 'regression'
                }
        
        return summary

def main():
    """Test the ML Training Pipeline"""
    print("🧠 MACHINE LEARNING TRAINING PIPELINE")
    print("="*60)
    
    # Initialize components
    preprocessor = MLDataPreprocessor()
    trainer = MLModelTrainer()
    
    # Test teams (smaller set for demonstration)
    test_teams = [
        "Manchester City", "Real Madrid", "Inter", "Bayern München", 
        "Arsenal", "Barcelona", "Liverpool", "Chelsea"
    ]
    
    print(f"🔄 Step 1: Data Collection and Preprocessing")
    
    # Collect training data
    training_df = preprocessor.collect_training_data(test_teams, num_samples=30)
    
    if len(training_df) == 0:
        print("❌ No training data collected")
        return
    
    print(f"📊 Training dataset shape: {training_df.shape}")
    
    # Prepare features and targets
    X, targets = trainer.prepare_features(training_df)
    
    print(f"🔄 Step 2: Model Training")
    
    # Train models
    match_model = trainer.train_match_outcome_model(X, targets['match_result'])
    goals_model = trainer.train_goals_model(X, targets['total_goals'])
    market_models = trainer.train_market_models(X, targets)
    
    print(f"🔄 Step 3: Model Persistence")
    
    # Save models
    trainer.save_models()
    
    # Get summary
    summary = trainer.get_model_summary()
    
    print(f"\n📋 ML TRAINING SUMMARY")
    print("="*40)
    print(f"✅ Total Models Trained: {summary['total_models']}")
    print(f"✅ Features Used: {summary['feature_count']}")
    
    print(f"\n📊 Model Performance:")
    for model_name, metrics in summary['models'].items():
        if metrics['type'] == 'classification':
            print(f"   {model_name}: {metrics['accuracy']:.3f} accuracy")
        else:
            print(f"   {model_name}: {metrics['r2_score']:.3f} R² score")
    
    print(f"\n🎯 Feature Importance (Top 5):")
    if 'match_outcome' in trainer.models:
        importance = trainer.models['match_outcome']['feature_importance']
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        for feature, score in top_features:
            print(f"   {feature}: {score:.3f}")
    
    print(f"\n✅ Machine Learning Pipeline completed successfully!")

if __name__ == "__main__":
    main()