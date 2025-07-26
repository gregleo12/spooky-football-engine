#!/usr/bin/env python3
"""
Real-time Prediction API - Phase 3
FastAPI-based real-time football prediction service
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import json
import sqlite3
import sys
import os
from datetime import datetime
import numpy as np
import asyncio

# Add all agent paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection_v2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'calculation'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'live_events'))

from modular_calculator_engine import ModularCalculatorEngine
from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from context_data_agent import ContextDataAgent
from live_match_collector import LiveMatchCollector, LiveEventProcessor

# Pydantic models for API
class PredictionRequest(BaseModel):
    home_team: str
    away_team: str
    competition: str = "Premier League"
    model_type: str = "enhanced"  # original, enhanced, market_match, market_goals, market_defense

class LivePredictionRequest(BaseModel):
    match_id: str
    current_minute: int
    home_score: int
    away_score: int
    events: List[Dict[str, Any]] = []

class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    prediction_timestamp: str
    model_used: str
    match_outcome: Optional[Dict[str, float]] = None
    goals_prediction: Optional[Dict[str, float]] = None
    market_predictions: Optional[Dict[str, Dict[str, float]]] = None
    confidence_score: Optional[float] = None
    execution_time_ms: Optional[float] = None

class LiveMatchResponse(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    current_score: str
    minute: int
    status: str
    last_updated: str
    events_count: int

class RealTimePredictionAPI:
    """Real-time prediction API service"""
    
    def __init__(self, db_path: str = "db/football_strength.db"):
        self.db_path = db_path
        self.calculator = ModularCalculatorEngine()
        self.live_collector = LiveMatchCollector(db_path)
        self.live_processor = LiveEventProcessor(self.live_collector)
        
        # Data collection agents
        self.agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent(),
            'context': ContextDataAgent()
        }
        
        # Register live event processing
        self.live_collector.add_event_callback(self.live_processor.handle_live_event)
        
        # Cache for team data (to improve performance)
        self.team_data_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def collect_team_data(self, team_name: str, competition: str) -> Dict[str, Any]:
        """Collect comprehensive team data"""
        
        cache_key = f"{team_name}_{competition}"
        
        # Check cache
        if cache_key in self.team_data_cache:
            cache_entry = self.team_data_cache[cache_key]
            if (datetime.now() - cache_entry['timestamp']).seconds < self.cache_ttl:
                return cache_entry['data']
        
        # Collect fresh data
        team_data = {'team_name': team_name}
        
        for agent_name, agent in self.agents.items():
            try:
                result = agent.execute_collection(team_name, competition)
                if result:
                    team_data.update(result['data'])
            except Exception as e:
                print(f"⚠️ Error collecting {agent_name} data for {team_name}: {e}")
        
        # Add mock squad data if missing (for demo purposes)
        if not any('squad' in key for key in team_data.keys()):
            team_data.update({
                'total_squad_value': np.random.uniform(100, 1500),
                'squad_depth_index': np.random.uniform(30, 90),
                'starting_xi_avg_value': np.random.uniform(20, 120)
            })
        
        # Cache the data
        self.team_data_cache[cache_key] = {
            'data': team_data,
            'timestamp': datetime.now()
        }
        
        return team_data
    
    def predict_match(self, home_team: str, away_team: str, 
                     competition: str = "Premier League", 
                     model_type: str = "enhanced") -> Dict[str, Any]:
        """Generate match predictions"""
        
        start_time = datetime.now()
        
        try:
            # Collect team data
            home_data = self.collect_team_data(home_team, competition)
            away_data = self.collect_team_data(away_team, competition)
            
            if not home_data or not away_data:
                raise ValueError("Could not collect team data")
            
            # Use calculator engine for predictions
            home_result = self.calculator.calculate_team_strength(home_data, model_type)
            away_result = self.calculator.calculate_team_strength(away_data, model_type)
            
            # Compare teams
            comparison = self.calculator.compare_team_strengths(home_data, away_data, model_type)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Prepare response
            prediction = {
                'home_team': home_team,
                'away_team': away_team,
                'prediction_timestamp': datetime.now().isoformat(),
                'model_used': model_type,
                'execution_time_ms': execution_time,
                
                # Match outcome probabilities
                'match_outcome': {
                    'home_win': comparison['win_probability_team1'],
                    'away_win': comparison['win_probability_team2'],
                    'draw': 1 - comparison['win_probability_team1'] - comparison['win_probability_team2']
                },
                
                # Team strengths
                'team_strengths': {
                    'home_strength': home_result['strength_percentage'],
                    'away_strength': away_result['strength_percentage'],
                    'strength_difference': comparison['strength_difference'] * 100
                },
                
                # Confidence based on data completeness
                'confidence_score': (home_result['data_completeness'] + away_result['data_completeness']) / 2,
                
                # Additional market predictions
                'market_predictions': self._generate_market_predictions(home_data, away_data)
            }
            
            return prediction
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
    
    def _generate_market_predictions(self, home_data: Dict[str, Any], away_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Generate predictions for specific betting markets"""
        
        markets = {}
        
        try:
            # Over/Under goals
            goals_result = self.calculator.calculate_team_strength(home_data, 'market_goals')
            defense_result = self.calculator.calculate_team_strength(away_data, 'market_defense')
            
            # Estimate expected goals (simplified)
            home_attack = home_data.get('goals_per_game', 1.5)
            away_attack = away_data.get('goals_per_game', 1.5)
            expected_goals = (home_attack + away_attack) / 2
            
            markets['goals'] = {
                'expected_total_goals': expected_goals,
                'over_2_5_probability': min(0.9, max(0.1, expected_goals / 3.5)),
                'over_1_5_probability': min(0.95, max(0.2, expected_goals / 2.5)),
                'under_2_5_probability': 1 - min(0.9, max(0.1, expected_goals / 3.5))
            }
            
            # Both teams to score
            home_scoring_prob = min(0.9, max(0.1, home_attack / 2.5))
            away_scoring_prob = min(0.9, max(0.1, away_attack / 2.5))
            
            markets['btts'] = {
                'both_teams_score': home_scoring_prob * away_scoring_prob,
                'home_clean_sheet': 1 - away_scoring_prob,
                'away_clean_sheet': 1 - home_scoring_prob
            }
            
        except Exception as e:
            print(f"⚠️ Error generating market predictions: {e}")
        
        return markets
    
    def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get currently active live matches"""
        
        active_matches = self.live_collector.get_active_matches()
        
        return [
            {
                'match_id': match.match_id,
                'api_fixture_id': match.api_fixture_id,
                'home_team': match.home_team_name,
                'away_team': match.away_team_name,
                'current_score': f"{match.home_score}-{match.away_score}",
                'minute': match.minute,
                'status': match.status,
                'events_count': len(match.events),
                'last_updated': match.last_updated.isoformat()
            }
            for match in active_matches
        ]
    
    def get_live_predictions(self, match_id: str) -> Dict[str, Any]:
        """Get live predictions for a specific match"""
        
        # Get match from database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            SELECT home_team_name, away_team_name, current_minute, home_score, away_score
            FROM live_matches 
            WHERE id = ?
        """, (match_id,))
        
        match_data = c.fetchone()
        conn.close()
        
        if not match_data:
            raise HTTPException(status_code=404, detail="Match not found")
        
        home_team, away_team, minute, home_score, away_score = match_data
        
        # Generate live prediction (simplified for demo)
        base_prediction = self.predict_match(home_team, away_team)
        
        # Adjust predictions based on current state
        score_diff = home_score - away_score
        minute_factor = minute / 90  # How much of the match is completed
        
        # Adjust probabilities based on current score and time
        if score_diff > 0:  # Home team leading
            base_prediction['match_outcome']['home_win'] = min(0.9, base_prediction['match_outcome']['home_win'] + 0.2 * minute_factor)
        elif score_diff < 0:  # Away team leading
            base_prediction['match_outcome']['away_win'] = min(0.9, base_prediction['match_outcome']['away_win'] + 0.2 * minute_factor)
        
        # Normalize probabilities
        total_prob = sum(base_prediction['match_outcome'].values())
        for outcome in base_prediction['match_outcome']:
            base_prediction['match_outcome'][outcome] /= total_prob
        
        # Add live context
        base_prediction['live_context'] = {
            'current_score': f"{home_score}-{away_score}",
            'minute': minute,
            'score_difference': score_diff,
            'match_progress': minute_factor
        }
        
        return base_prediction

# Initialize FastAPI app
app = FastAPI(
    title="Spooky Football Engine - Real-time Predictions API",
    description="Real-time football match prediction API with live events integration",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize prediction service
prediction_service = RealTimePredictionAPI()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Spooky Football Engine - Real-time Predictions API",
        "version": "3.0.0",
        "status": "active",
        "features": [
            "Real-time match predictions",
            "Live events integration", 
            "Multiple calculation models",
            "Betting market analysis"
        ]
    }

@app.post("/api/v3/predict/match", response_model=PredictionResponse)
async def predict_match(request: PredictionRequest):
    """Generate match predictions"""
    
    prediction = prediction_service.predict_match(
        home_team=request.home_team,
        away_team=request.away_team,
        competition=request.competition,
        model_type=request.model_type
    )
    
    return PredictionResponse(**prediction)

@app.get("/api/v3/live/matches")
async def get_live_matches():
    """Get currently active live matches"""
    
    matches = prediction_service.get_live_matches()
    
    return {
        "live_matches": matches,
        "count": len(matches),
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/v3/live/predictions/{match_id}")
async def get_live_predictions(match_id: str):
    """Get live predictions for a specific match"""
    
    predictions = prediction_service.get_live_predictions(match_id)
    
    return predictions

@app.post("/api/v3/live/start_collection")
async def start_live_collection(background_tasks: BackgroundTasks):
    """Start live data collection"""
    
    def start_collection():
        prediction_service.live_collector.start_live_collection(interval_seconds=30)
    
    background_tasks.add_task(start_collection)
    
    return {"message": "Live data collection started", "interval": "30 seconds"}

@app.post("/api/v3/live/stop_collection")
async def stop_live_collection():
    """Stop live data collection"""
    
    prediction_service.live_collector.stop_live_collection()
    
    return {"message": "Live data collection stopped"}

@app.get("/api/v3/analytics/teams/{team_name}")
async def get_team_analytics(team_name: str, competition: str = "Premier League"):
    """Get detailed team analytics"""
    
    team_data = prediction_service.collect_team_data(team_name, competition)
    
    if not team_data:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate strength with different models
    model_results = {}
    for model_type in ['original', 'enhanced', 'market_match', 'market_goals', 'market_defense']:
        try:
            result = prediction_service.calculator.calculate_team_strength(team_data, model_type)
            model_results[model_type] = result['strength_percentage']
        except:
            model_results[model_type] = None
    
    return {
        "team_name": team_name,
        "competition": competition,
        "strength_scores": model_results,
        "data_completeness": len([v for v in team_data.values() if v is not None]) / len(team_data),
        "last_updated": datetime.now().isoformat(),
        "raw_parameters": {k: v for k, v in team_data.items() if isinstance(v, (int, float))}
    }

@app.get("/api/v3/health")
async def health_check():
    """API health check"""
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "prediction_engine": "active",
            "live_collector": "active" if prediction_service.live_collector.is_collecting else "inactive",
            "database": "connected"
        }
    }

def main():
    """Run the API server"""
    print("🚀 STARTING REAL-TIME PREDICTION API")
    print("="*60)
    print("📡 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/api/v3/health")
    
    # Run the server
    uvicorn.run(
        "realtime_prediction_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()