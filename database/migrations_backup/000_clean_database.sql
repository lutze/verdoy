-- Drop all tables and extensions
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;

    -- Drop all extensions
    DROP EXTENSION IF EXISTS timescaledb CASCADE;
    DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;
END $$; 