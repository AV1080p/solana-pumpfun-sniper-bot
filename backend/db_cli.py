#!/usr/bin/env python3
"""
Database Management CLI

Usage:
    python db_cli.py init [--drop]
    python db_cli.py backup [--name BACKUP_NAME]
    python db_cli.py restore BACKUP_PATH [--drop]
    python db_cli.py list-backups
    python db_cli.py stats
    python db_cli.py health
    python db_cli.py optimize
"""
import argparse
import json
import sys
from db_utils import DatabaseManager


def main():
    parser = argparse.ArgumentParser(description="Database Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--drop", action="store_true", help="Drop existing tables first")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup database")
    backup_parser.add_argument("--name", help="Custom backup name")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database from backup")
    restore_parser.add_argument("backup_path", help="Path to backup file")
    restore_parser.add_argument("--drop", action="store_true", help="Drop existing objects first")
    
    # List backups command
    subparsers.add_parser("list-backups", help="List all backups")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    # Health check command
    subparsers.add_parser("health", help="Perform health check")
    
    # Optimize command
    subparsers.add_parser("optimize", help="Optimize database")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = DatabaseManager()
    
    try:
        if args.command == "init":
            result = manager.initialize_database(drop_existing=args.drop)
            print(json.dumps(result, indent=2))
            
        elif args.command == "backup":
            result = manager.backup_database(backup_name=args.name)
            print(json.dumps(result, indent=2))
            
        elif args.command == "restore":
            result = manager.restore_database(args.backup_path, drop_existing=args.drop)
            print(json.dumps(result, indent=2))
            
        elif args.command == "list-backups":
            backups = manager.list_backups()
            print(json.dumps(backups, indent=2))
            
        elif args.command == "stats":
            stats = manager.get_table_stats()
            print(json.dumps(stats, indent=2))
            
        elif args.command == "health":
            health = manager.health_check()
            print(json.dumps(health, indent=2))
            
        elif args.command == "optimize":
            result = manager.optimize_database()
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

