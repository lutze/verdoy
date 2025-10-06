#!/usr/bin/env python3
"""
Migration status checker for VerdoyLab database.
Shows which migrations are applied, pending, or rolled back.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_migration_files():
    """Get all SQL migration files in order, excluding rollback files."""
    migrations_dir = Path(__file__).parent / "migrations"
    return sorted(f for f in migrations_dir.glob("*.sql") if "_rollback" not in f.name)

def get_applied_migrations(conn):
    """Get list of already applied migrations with their status."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT version, status, applied_at, rolled_back_at, rollback_reason 
            FROM schema_migrations 
            ORDER BY applied_at
        """)
        return {row[0]: {
            'status': row[1],
            'applied_at': row[2],
            'rolled_back_at': row[3],
            'rollback_reason': row[4]
        } for row in cur.fetchall()}

def check_migrations():
    """Check and display migration status."""
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "myapp"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        migration_files = get_migration_files()
        applied_migrations = get_applied_migrations(conn)
        
        print("=== Migration Status Report ===\n")
        
        # Show all migration files and their status
        print("Migration Files:")
        print("-" * 80)
        for migration_file in migration_files:
            version = migration_file.stem
            if version in applied_migrations:
                status_info = applied_migrations[version]
                status = status_info['status']
                applied_at = status_info['applied_at']
                
                if status == 'rolled_back':
                    rolled_back_at = status_info['rolled_back_at']
                    reason = status_info['rollback_reason']
                    print(f"❌ {migration_file.name:<40} | {status:<12} | Applied: {applied_at} | Rolled back: {rolled_back_at}")
                    if reason:
                        print(f"   └─ Reason: {reason}")
                else:
                    print(f"✅ {migration_file.name:<40} | {status:<12} | Applied: {applied_at}")
            else:
                print(f"⏳ {migration_file.name:<40} | PENDING")
        
        print("\n" + "=" * 80)
        
        # Summary
        total_migrations = len(migration_files)
        applied_count = len([m for m in applied_migrations.values() if m['status'] == 'applied'])
        rolled_back_count = len([m for m in applied_migrations.values() if m['status'] == 'rolled_back'])
        pending_count = total_migrations - len(applied_migrations)
        
        print(f"Summary:")
        print(f"  Total migrations: {total_migrations}")
        print(f"  Applied: {applied_count}")
        print(f"  Rolled back: {rolled_back_count}")
        print(f"  Pending: {pending_count}")
        
        if pending_count > 0:
            print(f"\n⚠️  {pending_count} migration(s) pending. Run 'python database/setup_db.py' to apply.")
        
        if rolled_back_count > 0:
            print(f"\n⚠️  {rolled_back_count} migration(s) rolled back. Check rollback reasons above.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking migrations: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_migrations() 