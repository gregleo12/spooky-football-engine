#!/usr/bin/env python3
"""
Environment Configuration Module
Clear separation between local development and Railway production
"""
import os
from enum import Enum

class Environment(Enum):
    LOCAL = "local"
    RAILWAY = "railway"
    TESTING = "testing"

class EnvironmentConfig:
    """Central environment detection and configuration"""
    
    def __init__(self):
        self._environment = self._detect_environment()
        self._setup_environment_specific_config()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        
        # Railway specific detection
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            return Environment.RAILWAY
        
        # Alternative Railway detection methods
        if os.environ.get('DATABASE_URL') and 'railway' in os.environ.get('DATABASE_URL', ''):
            return Environment.RAILWAY
        
        # Check for Railway-specific environment variables
        railway_indicators = [
            'RAILWAY_PROJECT_ID',
            'RAILWAY_SERVICE_ID',
            'RAILWAY_DEPLOYMENT_ID'
        ]
        
        if any(os.environ.get(var) for var in railway_indicators):
            return Environment.RAILWAY
        
        # Check if running in production (has DATABASE_URL but not Railway)
        if os.environ.get('DATABASE_URL'):
            return Environment.RAILWAY  # Assume any DATABASE_URL is production
        
        # Testing environment
        if os.environ.get('TESTING') == 'true':
            return Environment.TESTING
        
        # Default to local
        return Environment.LOCAL
    
    def _setup_environment_specific_config(self):
        """Setup environment-specific configurations"""
        
        if self.is_railway():
            # Railway production settings
            self.database_type = "postgresql"
            self.database_path = None  # Use DATABASE_URL
            self.debug_mode = False
            self.use_file_storage = False
            self.enable_live_collectors = True  # But use database-based approach
            self.api_timeout = 30
            self.max_workers = 2
            
        elif self.is_local():
            # Local development settings
            self.database_type = "sqlite"
            self.database_path = "db/football_strength.db"
            self.debug_mode = True
            self.use_file_storage = True
            self.enable_live_collectors = True
            self.api_timeout = 60
            self.max_workers = 1
            
        else:  # Testing
            self.database_type = "sqlite"
            self.database_path = ":memory:"
            self.debug_mode = False
            self.use_file_storage = False
            self.enable_live_collectors = False
            self.api_timeout = 10
            self.max_workers = 1
    
    @property
    def environment(self) -> Environment:
        """Get current environment"""
        return self._environment
    
    def is_local(self) -> bool:
        """Check if running locally"""
        return self._environment == Environment.LOCAL
    
    def is_railway(self) -> bool:
        """Check if running on Railway"""
        return self._environment == Environment.RAILWAY
    
    def is_testing(self) -> bool:
        """Check if in testing mode"""
        return self._environment == Environment.TESTING
    
    def get_database_config(self) -> dict:
        """Get database configuration for current environment"""
        return {
            'type': self.database_type,
            'path': self.database_path,
            'url': os.environ.get('DATABASE_URL') if self.is_railway() else None,
            'use_postgresql': self.is_railway()
        }
    
    def get_phase3_config(self) -> dict:
        """Get Phase 3 configuration for current environment"""
        return {
            'enable_live_collectors': self.enable_live_collectors and self.is_local(),
            'enable_ml_features': True,
            'enable_api_endpoints': True,
            'use_database_queries': self.is_railway(),
            'use_file_collectors': self.is_local()
        }
    
    def log_environment_info(self):
        """Log current environment configuration"""
        print(f"🌍 Environment: {self.environment.value.upper()}")
        print(f"🗄️  Database: {self.database_type}")
        print(f"🐞 Debug: {self.debug_mode}")
        print(f"📁 File Storage: {self.use_file_storage}")
        print(f"⚡ Live Collectors: {self.enable_live_collectors}")
        
        if self.is_railway():
            print("🚀 Railway Production Mode")
            print("   • PostgreSQL database queries")
            print("   • No file system dependencies")
            print("   • Database-based live events")
        
        elif self.is_local():
            print("💻 Local Development Mode")
            print("   • SQLite file database")
            print("   • Full live collectors enabled")
            print("   • File system access available")

# Global environment configuration
env_config = EnvironmentConfig()

# Convenience functions
def is_local() -> bool:
    return env_config.is_local()

def is_railway() -> bool:
    return env_config.is_railway()

def is_testing() -> bool:
    return env_config.is_testing()

def get_environment() -> Environment:
    return env_config.environment

def log_startup_info():
    """Log environment info at startup"""
    env_config.log_environment_info()