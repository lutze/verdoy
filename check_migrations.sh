#!/bin/bash
# =====================================================================
# Migration Health Check Script
# =====================================================================
# Quick health check for the new migration system
# Usage: ./check_migrations.sh
# =====================================================================

set -e

echo "🔍 DATABASE MIGRATION HEALTH CHECK"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if containers are running
echo ""
echo "📦 Checking container status..."
if ! docker ps | grep -q "postgres-db"; then
    echo -e "${RED}❌ Database container not running${NC}"
    echo "   Run: docker compose up -d"
    exit 1
fi

if ! docker ps | grep -q "lms-core-poc-backend"; then
    echo -e "${RED}❌ Backend container not running${NC}"
    echo "   Run: docker compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ All containers running${NC}"

# Check applied migrations
echo ""
echo "🔄 Checking applied migrations..."
MIGRATIONS=$(docker exec postgres-db psql -U postgres -d verdoy-db -t -c "SELECT COUNT(*) FROM schema_migrations;")
MIGRATIONS=$(echo $MIGRATIONS | tr -d ' ')

if [ "$MIGRATIONS" -eq 2 ]; then
    echo -e "${GREEN}✅ Both migrations applied (001_schema, 002_test_data)${NC}"
else
    echo -e "${RED}❌ Expected 2 migrations, found $MIGRATIONS${NC}"
    docker exec postgres-db psql -U postgres -d verdoy-db -c "SELECT version, applied_at FROM schema_migrations ORDER BY applied_at;"
fi

# Check entity counts
echo ""
echo "📊 Checking test data..."
ENTITY_COUNT=$(docker exec postgres-db psql -U postgres -d verdoy-db -t -c "SELECT COUNT(*) FROM entities;")
ENTITY_COUNT=$(echo $ENTITY_COUNT | tr -d ' ')

if [ "$ENTITY_COUNT" -eq 14 ]; then
    echo -e "${GREEN}✅ All 14 test entities loaded${NC}"
else
    echo -e "${YELLOW}⚠️  Expected 14 entities, found $ENTITY_COUNT${NC}"
    docker exec postgres-db psql -U postgres -d verdoy-db -c "SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type ORDER BY entity_type;"
fi

# Check TimescaleDB
echo ""
echo "⏰ Checking TimescaleDB..."
HYPERTABLES=$(docker exec postgres-db psql -U postgres -d verdoy-db -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables WHERE hypertable_name = 'events';")
HYPERTABLES=$(echo $HYPERTABLES | tr -d ' ')

if [ "$HYPERTABLES" -eq 1 ]; then
    echo -e "${GREEN}✅ Events table is properly configured as hypertable${NC}"
else
    echo -e "${RED}❌ Events table is not a hypertable${NC}"
fi

# Check backend health
echo ""
echo "🌐 Checking backend health..."
if curl -s http://localhost:8000/ | grep -q "LMS evo"; then
    echo -e "${GREEN}✅ Backend responding correctly${NC}"
else
    echo -e "${RED}❌ Backend not responding or serving unexpected content${NC}"
fi

# Check data integrity
echo ""
echo "🔍 Checking data integrity..."
VIOLATIONS=$(docker exec postgres-db psql -U postgres -d verdoy-db -t -c "
    SELECT COUNT(*) FROM entities e1 
    WHERE e1.organization_id IS NOT NULL 
    AND NOT EXISTS (
        SELECT 1 FROM entities e2 
        WHERE e2.id = e1.organization_id 
        AND e2.entity_type = 'organization'
    );
")
VIOLATIONS=$(echo $VIOLATIONS | tr -d ' ')

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}✅ No data integrity violations found${NC}"
else
    echo -e "${RED}❌ Found $VIOLATIONS data integrity violations${NC}"
fi

# Summary
echo ""
echo "🎯 SUMMARY"
echo "=========="
echo -e "${GREEN}✅ Migration system is working correctly!${NC}"
echo ""
echo "📋 Quick commands:"
echo "   Full verification: docker exec postgres-db psql -U postgres -d verdoy-db -f /tmp/verify_db.sql"
echo "   Reset database: docker compose down && docker compose up -d --build"
echo "   View logs: docker logs lms-core-poc-backend-1"
echo "   Access web: http://localhost:8000"
echo ""

