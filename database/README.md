# Database Migrations

This directory contains the database migrations for the LMS Core system.

## Migration Order

Migrations are applied in alphabetical order. Current order:

1. `000_create_migrations_table.sql` - Creates the migration tracking table
2. `000_clean_database.sql` - Cleans existing data (development only)
3. `000_extensions.sql` - Enables required PostgreSQL extensions
4. `001_initial_schema.sql` - Creates core tables (events, entities, relationships, schemas, processes)
5. `002_indexes.sql` - Adds performance indexes
6. `003_esp32_device_schema.sql` - Defines ESP32 device schema
7. `004_initial_data.sql` - Inserts demo data
8. `005_schema_validation.sql` - Validates schema consistency

## Running Migrations

To run the migrations, use Docker Compose:

```sh
# Clean and rebuild the database
docker compose down -v
docker compose up --build -d db-init

# Verify the schema
docker compose exec db psql -U postgres -d myapp -c '\dt'
```

This will apply all migrations in order and ensure the database is ready for use.

## Alternative ways to run migrations

### Automatic Setup
```bash
python database/setup_db.py
```

### Manual Migration
```bash
psql -d myapp -f database/migrations/XXX_migration_name.sql
```

## Rollback Process

### Manual Rollback
Rollback files are named with `_rollback` suffix and should be run manually:

```bash
psql -d myapp -f database/migrations/003_esp32_device_schema_rollback.sql
```

### Rollback Tracking
Rollbacks are tracked in the `schema_migrations` table with:
- `status`: 'applied' or 'rolled_back'
- `rolled_back_at`: Timestamp of rollback
- `rollback_reason`: Reason for rollback

## Migration Status

Check migration status:
```bash
python database/check_migrations.py
```

## Schema Design

### Graph-like Structure
- `entities`: All "things" in the system (devices, users, equipment)
- `relationships`: Connections between entities
- `events`: Immutable history of all changes
- `schemas`: Type definitions for entities

### Device Management
- Devices are stored as entities with `entity_type = 'device.esp32'`
- Device properties follow the schema defined in `003_esp32_device_schema.sql`
- Device ownership is tracked through relationships

## Best Practices

1. **Always test migrations** in development before production
2. **Use rollback files** for destructive changes
3. **Validate data** after schema changes
4. **Document changes** in migration comments
5. **Keep migrations atomic** - one logical change per file

## Troubleshooting

### Migration Fails
1. Check database connection
2. Verify migration file syntax
3. Check for conflicting data
4. Review migration order

### Rollback Issues
1. Ensure rollback file exists
2. Check for dependent data
3. Verify rollback order (reverse of migration order)
4. Review rollback logs in `schema_migrations` table 