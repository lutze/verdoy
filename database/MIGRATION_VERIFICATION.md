# Database Migration Verification Guide

This guide explains how to verify that our new streamlined migration system is working correctly.

## Quick Health Check

For a fast verification of the migration system:

```bash
./check_migrations.sh
```

This script checks:
- ✅ Container status (database and backend)
- ✅ Applied migrations (should show 2: schema + test data)
- ✅ Entity counts (should show 14 total entities)
- ✅ TimescaleDB configuration (events hypertable)
- ✅ Backend health (web interface responding)
- ✅ Data integrity (no orphaned records)

## Comprehensive Verification

For a detailed analysis of the database structure and data:

```bash
docker cp verify_db.sql postgres-db:/tmp/
docker exec postgres-db psql -U postgres -d lmsevo-db -f /tmp/verify_db.sql
```

This provides:
- 📋 Complete table and index inventory
- 🔗 Foreign key constraint verification
- ⏰ TimescaleDB feature validation
- 📊 Test data verification by entity type
- 🔍 Data integrity checks
- ⚙️ Function and trigger validation
- 👥 Sample data review (organizations, users, projects, devices)
- 📈 Database size and performance metrics

## Expected Results

### Migration Status
- **001_schema**: Complete database schema with all tables, indexes, constraints
- **002_test_data**: Comprehensive test data for development and testing

### Entity Counts
```
✅ device.bioreactor: 1     (Acme Bioreactor BR-001)
✅ device.esp32: 1          (DEMO ESP32 Node 042)
✅ equipment.oven: 1        (DEMO Production Oven #1)
✅ experiment: 1            (Recombinant Protein Production Study)
✅ organization: 3          (Acme Research Labs, BioTech Innovations, Default)
✅ project: 3               (Bioreactor Optimization, Fermentation Process, Sensor Network)
✅ user: 4                  (Test User, Dr. Sarah Johnson, Dr. Michael Chen, Alex Rodriguez)
```

### Supporting Data
- **Organization members**: 3 (proper membership relationships)
- **Processes**: 2 (Sourdough Bread Recipe, Fermentation Protocol)
- **Experiment trials**: 2 (1 completed, 1 running)
- **Relationships**: Device monitoring relationships
- **Schema definitions**: 3 (ESP32, sensor readings, baking process)

### TimescaleDB Features
- ✅ Events table configured as hypertable
- ✅ Time-based partitioning active
- ✅ Compression and retention policies ready

## Troubleshooting

### If Migrations Are Missing
```bash
# Check migration status
docker exec postgres-db psql -U postgres -d lmsevo-db -c "SELECT version, applied_at FROM schema_migrations;"

# Manually apply if needed
docker cp database/migrations/002_test_data.sql postgres-db:/tmp/
docker exec postgres-db psql -U postgres -d lmsevo-db -f /tmp/002_test_data.sql
```

### If Entity Counts Are Wrong
```bash
# Check what's in the database
docker exec postgres-db psql -U postgres -d lmsevo-db -c "SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;"

# Reset if needed
docker compose down
docker compose up -d --build
```

### If Backend Not Responding
```bash
# Check backend logs
docker logs lms-core-poc-backend-1

# Restart backend
docker compose restart backend
```

## Clean Rebuild Process

To test the migration system from scratch:

```bash
# 1. Stop all containers
docker compose down

# 2. Remove database volume (optional - for complete reset)
docker volume rm lms-core-poc_postgres_data

# 3. Rebuild with fresh database
docker compose up -d --build

# 4. Verify everything worked
./check_migrations.sh
```

## Files

- `check_migrations.sh` - Quick health check script
- `database/migrations/001_schema.sql` - Complete database schema
- `database/migrations/002_test_data.sql` - Comprehensive test data
- `database/migrations_backup/` - Backup of original migration files

## Migration System Benefits

✅ **Clean Setup**: 2 files instead of 21 scattered migrations  
✅ **Fast Deployment**: Complete database in seconds  
✅ **Easy Testing**: Quick verification with health check  
✅ **Clear Structure**: Separate schema from data  
✅ **Development Friendly**: Consistent test environment  
✅ **Production Ready**: Idempotent and error-handling  

The new migration system provides a reliable, fast, and maintainable approach to database setup for the LMS Evolution platform.
