#!/usr/bin/env python3
"""
Database Configuration Module
Handles both SQLite (local development) and PostgreSQL (production)
"""
import os
import sqlite3
import psycopg2
from contextlib import contextmanager

class DatabaseConfig:
    def __init__(self):
        # Check if we're in production (PostgreSQL) or development (SQLite)
        self.database_url = os.environ.get('DATABASE_URL')
        self.use_postgresql = bool(self.database_url)
        
        # SQLite fallback for local development
        self.sqlite_path = "db/football_strength.db"
        
    def get_connection(self):
        """Get appropriate database connection"""
        if self.use_postgresql:
            # Railway PostgreSQL doesn't require SSL
            # Don't use RealDictCursor to maintain compatibility with SQLite row access
            return psycopg2.connect(self.database_url)
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
    
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
            if self.use_postgresql:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if cursor.description:
                        return cursor.fetchall()
                    return None
            else:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                if cursor.description:
                    return cursor.fetchall()
                return None
    
    def execute_many(self, query, params_list):
        """Execute query with multiple parameter sets"""
        with self.get_db_connection() as conn:
            if self.use_postgresql:
                with conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    conn.commit()
            else:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
    
    def execute_transaction(self, queries_and_params):
        """Execute multiple queries in a transaction"""
        with self.get_db_connection() as conn:
            try:
                if self.use_postgresql:
                    with conn.cursor() as cursor:
                        for query, params in queries_and_params:
                            cursor.execute(query, params or ())
                        conn.commit()
                else:
                    cursor = conn.cursor()
                    for query, params in queries_and_params:
                        cursor.execute(query, params or ())
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_db_type(self):
        """Return database type for debugging"""
        return "PostgreSQL" if self.use_postgresql else "SQLite"

# Global database instance
db_config = DatabaseConfig()

# Convenience functions for backward compatibility
def get_database_connection():
    """Get database connection (backward compatibility)"""
    return db_config.get_connection()

def execute_query(query, params=None):
    """Execute query (backward compatibility)"""
    return db_config.execute_query(query, params)