import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time

def wait_for_db(db_params, max_retries=5, retry_interval=2):
    """Wait for the database to be ready."""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**db_params)
            conn.close()
            return True
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"Database not ready, retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                raise
    return False

def get_migration_files():
    """Get all SQL migration files in order, excluding rollback files."""
    migrations_dir = Path(__file__).parent / "migrations"
    # Get all .sql files, excluding those with _rollback in the name
    return sorted(f for f in migrations_dir.glob("*.sql") if "_rollback" not in f.name)

def get_applied_migrations(conn):
    """Get list of already applied migrations. Returns empty set if table does not exist."""
    with conn.cursor() as cur:
        # Check if schema_migrations table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            )
        """)
        exists = cur.fetchone()[0]
        if not exists:
            return set()
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}

def run_migrations(conn, migration_files, db_params):
    """Run all migration files in order."""
    applied_migrations = get_applied_migrations(conn)

    print("\n--- Migration files to be applied (in order) ---")
    for migration_file in migration_files:
        print(migration_file.name)
    print("--- Already applied migrations ---")
    for migration in applied_migrations:
        print(migration)
    print("---------------------------------------------\n")

    i = 0
    while i < len(migration_files):
        migration_file = migration_files[i]
        version = migration_file.stem
        if version in applied_migrations:
            print(f"Skipping already applied migration: {migration_file.name}")
            i += 1
            continue

        print(f"Running migration: {migration_file.name}")
        try:
            with open(migration_file) as f:
                sql = f.read()
                with psycopg2.connect(**db_params) as migration_conn:
                    migration_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    with migration_conn.cursor() as cur:
                        cur.execute(sql)
                        # Only track migrations except the clean database migration
                        if version != "000_clean_database":
                            try:
                                cur.execute(
                                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                                    (version,)
                                )
                            except psycopg2.IntegrityError as e:
                                if "duplicate key" in str(e).lower():
                                    print(f"Migration {version} already recorded, continuing...")
                                else:
                                    raise
            print(f"Completed migration: {migration_file.name}")

            # If we just ran the clean database migration, reconnect and reset state
            if version == "000_clean_database":
                print("Reconnecting and resetting migration state after clean...")
                with psycopg2.connect(**db_params) as conn2:
                    conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    get_applied_migrations(conn2)  # This will recreate schema_migrations
                applied_migrations = set()
                # Also, skip incrementing i so we re-check all migrations after clean
                i += 1
                continue

            applied_migrations.add(version)
            i += 1
        except Exception as e:
            print(f"Error running migration {migration_file.name}: {str(e)}")
            raise

def setup_database():
    """Set up the database with all migrations."""
    # Database connection parameters from docker-compose.yml
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "verdoy-db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    try:
        # Wait for database to be ready
        print("Waiting for database to be ready...")
        wait_for_db(db_params)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Run migrations
        migration_files = get_migration_files()
        if not migration_files:
            print("No migration files found!")
            return
        
        run_migrations(conn, migration_files, db_params)
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database() 