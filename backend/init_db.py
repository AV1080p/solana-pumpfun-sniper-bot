#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database by:
1. Creating all tables
2. Running seed data (if needed)

Usage:
    python init_db.py [--drop] [--seed]
"""
import argparse
import sys
from db_utils import DatabaseManager
from seed_data import seed_tours


def main():
    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables first")
    parser.add_argument("--seed", action="store_true", help="Seed initial data")
    
    args = parser.parse_args()
    
    print("Initializing database...")
    manager = DatabaseManager()
    
    # Initialize database
    result = manager.initialize_database(drop_existing=args.drop)
    
    if not result.get("success"):
        print(f"Error: {result.get('message')}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ Database initialized successfully")
    print(f"  Tables created: {', '.join(result.get('tables_created', []))}")
    
    # Seed data if requested
    if args.seed:
        print("\nSeeding initial data...")
        try:
            seed_tours()
            print("✓ Seed data loaded successfully")
        except Exception as e:
            print(f"Warning: Failed to seed data: {e}", file=sys.stderr)
    
    # Show database info
    print("\nDatabase Information:")
    db_info = manager.health_check()
    print(f"  Status: {'✓ Healthy' if db_info.get('healthy') else '✗ Unhealthy'}")
    print(f"  Connection: {'✓ Connected' if db_info.get('connection') else '✗ Disconnected'}")
    
    if db_info.get("table_stats", {}).get("success"):
        print("\nTable Statistics:")
        for table, stats in db_info["table_stats"]["tables"].items():
            if "row_count" in stats:
                print(f"  {table}: {stats['row_count']} rows")


if __name__ == "__main__":
    main()

