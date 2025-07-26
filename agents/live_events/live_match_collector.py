#!/usr/bin/env python3
"""
Live Match Events Data Collector - Phase 3
Captures real-time match events and updates predictions dynamically
"""
import requests
import json
import time
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import threading
from dataclasses import dataclass
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

@dataclass
class MatchEvent:
    """Represents a live match event"""
    event_id: str
    match_id: str
    minute: int
    event_type: str  # goal, card, substitution, etc.
    team_id: int
    player: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class LiveMatch:
    """Represents a live match state"""
    match_id: str
    api_fixture_id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    status: str
    minute: int
    home_score: int
    away_score: int
    events: List[MatchEvent]
    last_updated: datetime

class LiveMatchCollector:
    """Collects live match data and events from API-Football"""
    
    def __init__(self, db_path: str = "db/football_strength.db"):
        self.api_key = "53faec37f076f995841d30d0f7b2dd9d"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }
        self.db_path = db_path
        self.active_matches = {}
        self.event_callbacks = []
        self.is_collecting = False
        
        # Initialize database tables
        self._init_live_tables()
    
    def _init_live_tables(self):
        """Initialize database tables for live data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Live matches table
        c.execute("""
            CREATE TABLE IF NOT EXISTS live_matches (
                id TEXT PRIMARY KEY,
                api_fixture_id INTEGER UNIQUE,
                home_team_id INTEGER,
                away_team_id INTEGER,
                home_team_name TEXT,
                away_team_name TEXT,
                match_status TEXT,
                current_minute INTEGER,
                home_score INTEGER,
                away_score INTEGER,
                competition_id TEXT,
                kickoff_time DATETIME,
                last_event_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Live events table
        c.execute("""
            CREATE TABLE IF NOT EXISTS live_events (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                api_fixture_id INTEGER,
                event_minute INTEGER,
                event_type TEXT,
                team_id INTEGER,
                player_name TEXT,
                event_details TEXT,
                event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (match_id) REFERENCES live_matches(id)
            )
        """)
        
        # Live predictions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS live_predictions (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                prediction_minute INTEGER,
                home_win_prob REAL,
                draw_prob REAL,
                away_win_prob REAL,
                over_2_5_prob REAL,
                expected_goals REAL,
                prediction_model TEXT,
                prediction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (match_id) REFERENCES live_matches(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Live events database tables initialized")
    
    def get_live_fixtures(self, date: str = None) -> List[Dict[str, Any]]:
        """Get live fixtures for today or specified date"""
        
        url = f"{self.base_url}/fixtures"
        params = {
            'live': 'all'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                print(f"📡 Found {len(fixtures)} live fixtures")
                return fixtures
            else:
                print(f"❌ Error getting live fixtures: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting live fixtures: {e}")
            return []
    
    def get_fixture_events(self, fixture_id: int) -> List[Dict[str, Any]]:
        """Get live events for a specific fixture"""
        
        url = f"{self.base_url}/fixtures/events"
        params = {'fixture': fixture_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('response', [])
                return events
            else:
                print(f"❌ Error getting events for fixture {fixture_id}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting events for fixture {fixture_id}: {e}")
            return []
    
    def process_live_fixture(self, fixture_data: Dict[str, Any]) -> Optional[LiveMatch]:
        """Process a live fixture into a LiveMatch object"""
        
        try:
            fixture = fixture_data['fixture']
            teams = fixture_data['teams']
            goals = fixture_data['goals']
            
            match_id = str(uuid.uuid4())
            api_fixture_id = fixture['id']
            
            # Get events
            events_data = self.get_fixture_events(api_fixture_id)
            events = []
            
            for event_data in events_data:
                event = MatchEvent(
                    event_id=str(uuid.uuid4()),
                    match_id=match_id,
                    minute=event_data.get('time', {}).get('elapsed', 0),
                    event_type=event_data.get('type', 'unknown'),
                    team_id=event_data.get('team', {}).get('id', 0),
                    player=event_data.get('player', {}).get('name'),
                    details=event_data.get('detail'),
                    timestamp=datetime.now(timezone.utc)
                )
                events.append(event)
            
            live_match = LiveMatch(
                match_id=match_id,
                api_fixture_id=api_fixture_id,
                home_team_id=teams['home']['id'],
                away_team_id=teams['away']['id'],
                home_team_name=teams['home']['name'],
                away_team_name=teams['away']['name'],
                status=fixture['status']['short'],
                minute=fixture['status'].get('elapsed', 0) or 0,
                home_score=goals['home'] or 0,
                away_score=goals['away'] or 0,
                events=events,
                last_updated=datetime.now(timezone.utc)
            )
            
            return live_match
            
        except Exception as e:
            print(f"❌ Error processing fixture: {e}")
            return None
    
    def store_live_match(self, live_match: LiveMatch):
        """Store live match data in database"""
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Store/update match
            c.execute("""
                INSERT OR REPLACE INTO live_matches (
                    id, api_fixture_id, home_team_id, away_team_id,
                    home_team_name, away_team_name, match_status,
                    current_minute, home_score, away_score,
                    last_event_time, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                live_match.match_id,
                live_match.api_fixture_id,
                live_match.home_team_id,
                live_match.away_team_id,
                live_match.home_team_name,
                live_match.away_team_name,
                live_match.status,
                live_match.minute,
                live_match.home_score,
                live_match.away_score,
                live_match.last_updated.isoformat(),
                datetime.now().isoformat()
            ))
            
            # Store events
            for event in live_match.events:
                c.execute("""
                    INSERT OR IGNORE INTO live_events (
                        id, match_id, api_fixture_id, event_minute,
                        event_type, team_id, player_name, event_details,
                        event_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.match_id,
                    live_match.api_fixture_id,
                    event.minute,
                    event.event_type,
                    event.team_id,
                    event.player,
                    json.dumps(event.details) if event.details else None,
                    event.timestamp.isoformat() if event.timestamp else datetime.now().isoformat()
                ))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error storing live match: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def add_event_callback(self, callback):
        """Add callback function to be called when new events occur"""
        self.event_callbacks.append(callback)
    
    def _notify_event_callbacks(self, event: MatchEvent, match: LiveMatch):
        """Notify all registered callbacks of new events"""
        for callback in self.event_callbacks:
            try:
                callback(event, match)
            except Exception as e:
                print(f"⚠️ Error in event callback: {e}")
    
    def start_live_collection(self, interval_seconds: int = 30):
        """Start collecting live match data at regular intervals"""
        
        print(f"🚀 Starting live collection (every {interval_seconds}s)")
        self.is_collecting = True
        
        def collection_loop():
            while self.is_collecting:
                try:
                    self.collect_live_data()
                    time.sleep(interval_seconds)
                except Exception as e:
                    print(f"❌ Error in collection loop: {e}")
                    time.sleep(interval_seconds)
        
        # Start collection in background thread
        collection_thread = threading.Thread(target=collection_loop, daemon=True)
        collection_thread.start()
        
        return collection_thread
    
    def stop_live_collection(self):
        """Stop live data collection"""
        print("⏹️ Stopping live collection")
        self.is_collecting = False
    
    def collect_live_data(self):
        """Collect current live match data"""
        
        print("📡 Collecting live match data...")
        
        # Get live fixtures
        fixtures = self.get_live_fixtures()
        
        if not fixtures:
            print("   No live matches found")
            return
        
        new_events_count = 0
        
        for fixture_data in fixtures[:5]:  # Limit to 5 matches to avoid API limits
            live_match = self.process_live_fixture(fixture_data)
            
            if live_match:
                # Check for new events
                previous_match = self.active_matches.get(live_match.api_fixture_id)
                
                if previous_match:
                    # Find new events
                    previous_event_count = len(previous_match.events)
                    current_event_count = len(live_match.events)
                    
                    if current_event_count > previous_event_count:
                        new_events = live_match.events[previous_event_count:]
                        new_events_count += len(new_events)
                        
                        for event in new_events:
                            print(f"   🚨 NEW EVENT: {live_match.home_team_name} vs {live_match.away_team_name}")
                            print(f"      {event.minute}' {event.event_type} - {event.player}")
                            
                            # Notify callbacks
                            self._notify_event_callbacks(event, live_match)
                
                # Store updated match data
                self.store_live_match(live_match)
                self.active_matches[live_match.api_fixture_id] = live_match
                
                print(f"   📊 {live_match.home_team_name} {live_match.home_score}-{live_match.away_score} {live_match.away_team_name} ({live_match.minute}')")
        
        if new_events_count > 0:
            print(f"   ⚡ Processed {new_events_count} new events")
    
    def get_active_matches(self) -> List[LiveMatch]:
        """Get currently active matches"""
        return list(self.active_matches.values())
    
    def get_match_events(self, match_id: str) -> List[MatchEvent]:
        """Get events for a specific match"""
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            SELECT id, match_id, event_minute, event_type, team_id, 
                   player_name, event_details, event_timestamp
            FROM live_events 
            WHERE match_id = ? 
            ORDER BY event_minute, event_timestamp
        """, (match_id,))
        
        events = []
        for row in c.fetchall():
            event = MatchEvent(
                event_id=row[0],
                match_id=row[1],
                minute=row[2],
                event_type=row[3],
                team_id=row[4],
                player=row[5],
                details=json.loads(row[6]) if row[6] else None,
                timestamp=datetime.fromisoformat(row[7]) if row[7] else None
            )
            events.append(event)
        
        conn.close()
        return events

class LiveEventProcessor:
    """Processes live events and triggers prediction updates"""
    
    def __init__(self, collector: LiveMatchCollector):
        self.collector = collector
        self.prediction_triggers = {
            'Goal': self.handle_goal_event,
            'Card': self.handle_card_event,
            'subst': self.handle_substitution_event
        }
    
    def handle_live_event(self, event: MatchEvent, match: LiveMatch):
        """Handle a live event and trigger appropriate actions"""
        
        print(f"⚡ Processing live event: {event.event_type} at {event.minute}'")
        
        # Trigger prediction update based on event type
        if event.event_type in self.prediction_triggers:
            self.prediction_triggers[event.event_type](event, match)
        
        # Always update predictions for significant events
        if event.event_type in ['Goal', 'Card']:
            self.trigger_prediction_update(match)
    
    def handle_goal_event(self, event: MatchEvent, match: LiveMatch):
        """Handle goal events"""
        print(f"   ⚽ GOAL! {event.player} ({event.minute}')")
        
        # Goals significantly change match dynamics
        self.trigger_prediction_update(match, priority='high')
    
    def handle_card_event(self, event: MatchEvent, match: LiveMatch):
        """Handle card events"""
        print(f"   🟨 CARD! {event.player} ({event.minute}')")
        
        # Red cards are more significant than yellow cards
        if 'Red' in str(event.details):
            self.trigger_prediction_update(match, priority='high')
        else:
            self.trigger_prediction_update(match, priority='medium')
    
    def handle_substitution_event(self, event: MatchEvent, match: LiveMatch):
        """Handle substitution events"""
        print(f"   🔄 SUB! {event.player} ({event.minute}')")
        
        # Substitutions have moderate impact
        self.trigger_prediction_update(match, priority='low')
    
    def trigger_prediction_update(self, match: LiveMatch, priority: str = 'medium'):
        """Trigger a prediction update for the match"""
        
        print(f"   🔮 Triggering prediction update (priority: {priority})")
        
        # Store prediction trigger
        conn = sqlite3.connect(self.collector.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO live_predictions (
                id, match_id, prediction_minute, prediction_model, prediction_timestamp
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            match.match_id,
            match.minute,
            f'live_update_{priority}',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

def main():
    """Test the Live Match Collector"""
    print("📡 LIVE MATCH EVENTS COLLECTOR TEST")
    print("="*60)
    
    # Initialize collector
    collector = LiveMatchCollector()
    processor = LiveEventProcessor(collector)
    
    # Register event processor
    collector.add_event_callback(processor.handle_live_event)
    
    print("🔄 Testing live data collection...")
    
    # Test single collection
    collector.collect_live_data()
    
    # Show active matches
    active_matches = collector.get_active_matches()
    print(f"\n📊 Active matches: {len(active_matches)}")
    
    for match in active_matches:
        print(f"   {match.home_team_name} {match.home_score}-{match.away_score} {match.away_team_name}")
        print(f"   Status: {match.status}, Minute: {match.minute}")
        print(f"   Events: {len(match.events)}")
    
    # Start continuous collection for demonstration
    if active_matches:
        print(f"\n🚀 Starting live collection for 60 seconds...")
        collection_thread = collector.start_live_collection(interval_seconds=20)
        
        # Run for 60 seconds
        time.sleep(60)
        
        collector.stop_live_collection()
        print("⏹️ Live collection stopped")
    else:
        print("   No live matches to track")
    
    print(f"\n✅ Live Match Events Collector test completed!")

if __name__ == "__main__":
    main()