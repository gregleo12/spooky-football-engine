#!/usr/bin/env python3
"""
Database Configuration Module
Handles PostgreSQL connections for both local development and production
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class DatabaseConfig:
    def __init__(self):
        # Check if we're in production (Railway) or local development
        self.database_url = os.environ.get('DATABASE_URL')
        self.use_production = bool(self.database_url)
        
        # Local PostgreSQL configuration
        self.local_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'football_strength',
            'user': 'football_user',
            'password': 'local_dev_password'
        }
        
        # For backward compatibility with agents
        self.use_postgresql = True  # Always True now
        
    def get_connection(self):
        """Get appropriate database connection"""
        if self.use_production:
            # Railway PostgreSQL (production)
            return psycopg2.connect(self.database_url)
        else:
            # Local PostgreSQL (development)
            return psycopg2.connect(**self.local_config)
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if cursor.description:
                    return cursor.fetchall()
                return None
    
    def execute_many(self, query, params_list):
        """Execute query with multiple parameter sets"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
    
    def execute_transaction(self, queries_and_params):
        """Execute multiple queries in a transaction"""
        with self.get_db_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    for query, params in queries_and_params:
                        cursor.execute(query, params or ())
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_db_type(self):
        """Return database type for debugging"""
        return "PostgreSQL (Production)" if self.use_production else "PostgreSQL (Local)"
    
    def get_db_info(self):
        """Get database connection info for debugging"""
        if self.use_production:
            return f"Connected to Railway PostgreSQL"
        else:
            return f"Connected to Local PostgreSQL at {self.local_config['host']}:{self.local_config['port']}"

# Global database instance
db_config = DatabaseConfig()

# Convenience functions for backward compatibility
def get_database_connection():
    """Get database connection (backward compatibility)"""
    return db_config.get_connection()

def execute_query(query, params=None):
    """Execute query (backward compatibility)"""
    return db_config.execute_query(query, params)

# For agents that need to check database type
def get_db_connection():
    """Alias for backward compatibility with agents"""
    return db_config.get_connection()

# Property for agents checking database type
use_postgresql = True  # Always True now since we only use PostgreSQL