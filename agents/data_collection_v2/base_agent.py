#!/usr/bin/env python3
"""
Base Data Collection Agent
Foundation class for all Phase 1 data collection agents
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

class BaseDataAgent(ABC):
    """Base class for all data collection agents in Phase 1"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.last_execution = None
        self.execution_count = 0
        
    @abstractmethod
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect data for a specific team in a specific competition
        
        Args:
            team_id: Unique team identifier
            competition_id: Competition identifier
            
        Returns:
            Dictionary containing collected data with metadata
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected data for quality and completeness
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            True if data passes validation, False otherwise
        """
        pass
    
    def get_data_age_days(self, last_updated: datetime) -> int:
        """Calculate age of data in days"""
        if not last_updated:
            return 999  # Very old if no timestamp
        return (datetime.now() - last_updated).days
    
    def is_data_fresh(self, last_updated: datetime, max_age_days: int = 7) -> bool:
        """Check if data is fresh enough"""
        return self.get_data_age_days(last_updated) <= max_age_days
    
    def create_data_package(self, raw_data: Dict[str, Any], 
                          confidence: float = 1.0,
                          data_source: str = "unknown") -> Dict[str, Any]:
        """
        Create standardized data package with metadata
        
        Args:
            raw_data: The actual collected data
            confidence: Quality confidence (0-1)
            data_source: Source of the data
            
        Returns:
            Standardized data package
        """
        return {
            'data': raw_data,
            'metadata': {
                'agent_name': self.agent_name,
                'collection_timestamp': datetime.now(),
                'confidence_level': confidence,
                'data_source': data_source,
                'execution_count': self.execution_count
            }
        }
    
    def log_execution(self, success: bool, message: str = ""):
        """Log agent execution for monitoring"""
        self.last_execution = datetime.now()
        self.execution_count += 1
        status = "✅" if success else "❌"
        print(f"{status} {self.agent_name}: {message}")
    
    def execute_collection(self, team_id: str, competition_id: str) -> Optional[Dict[str, Any]]:
        """
        Main execution method with error handling and logging
        
        Args:
            team_id: Team to collect data for
            competition_id: Competition context
            
        Returns:
            Data package or None if collection failed
        """
        try:
            print(f"🔄 {self.agent_name}: Collecting data for team {team_id} in competition {competition_id}")
            
            # Collect the data
            raw_data = self.collect_data(team_id, competition_id)
            
            # Validate the data
            if not self.validate_data(raw_data):
                self.log_execution(False, f"Data validation failed for team {team_id}")
                return None
            
            # Create data package
            data_package = self.create_data_package(raw_data)
            
            self.log_execution(True, f"Successfully collected data for team {team_id}")
            return data_package
            
        except Exception as e:
            self.log_execution(False, f"Error collecting data for team {team_id}: {str(e)}")
            return None


class DataCollectionError(Exception):
    """Custom exception for data collection issues"""
    pass


class DataValidationError(Exception):
    """Custom exception for data validation issues"""
    pass