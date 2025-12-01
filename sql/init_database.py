#!/usr/bin/env python3
"""
Initialize DuckDB database with schema
"""

import duckdb
import os

def init_database(db_path='data/processed/spotify.duckdb'):
    """Create database and tables"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database (creates if doesn't exist)
    conn = duckdb.connect(db_path)
    
    # Read and execute schema
    with open('sql/create_schema.sql', 'r') as f:
        schema_sql = f.read()
        conn.execute(schema_sql)
    
    print(f"✓ Database initialized at {db_path}")
    
    # Show created tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"\nCreated {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    init_database()