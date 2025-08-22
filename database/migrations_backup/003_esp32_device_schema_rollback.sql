-- IMPORTANT: This is a rollback migration that should be run manually
-- Usage: psql -d myapp -f 003_esp32_device_schema_rollback.sql
-- This will roll back the ESP32 device schema and test data

-- Migration: Rollback ESP32 device schema
-- Description: Rolls back the ESP32 device schema and test data

DO $$
DECLARE
    test_device_id UUID;
BEGIN
    -- 1. Mark the schema as invalid
    UPDATE schemas 
    SET valid_to = CURRENT_TIMESTAMP
    WHERE id = 'device.esp32.v1';

    -- 2. Get the test device ID
    SELECT id INTO test_device_id 
    FROM entities 
    WHERE name = 'Test ESP32 Device' 
    AND entity_type = 'device.esp32';

    -- 3. If test device exists, soft delete it
    IF test_device_id IS NOT NULL THEN
        -- Update the device status to deleted
        UPDATE entities 
        SET status = 'deleted',
            properties = properties || jsonb_build_object(
                'deleted_at', CURRENT_TIMESTAMP,
                'deletion_reason', 'Test data cleanup'
            )
        WHERE id = test_device_id;

        -- Add an event recording the deletion
        INSERT INTO events (event_type, entity_id, entity_type, data) VALUES
        (
            'device.deleted',
            test_device_id,
            'device.esp32',
            jsonb_build_object(
                'name', 'Test ESP32 Device',
                'deleted_at', CURRENT_TIMESTAMP,
                'deletion_reason', 'Test data cleanup'
            )
        );
    END IF;

    -- 4. Add an event recording the schema deprecation
    INSERT INTO events (event_type, entity_type, data) VALUES
    (
        'schema.deprecated',
        'device.esp32',
        jsonb_build_object(
            'schema_id', 'device.esp32.v1',
            'deprecated_at', CURRENT_TIMESTAMP,
            'reason', 'Test data cleanup'
        )
    );

    -- 5. Update the migration record to indicate rollback
    UPDATE schema_migrations 
    SET status = 'rolled_back',
        rolled_back_at = CURRENT_TIMESTAMP,
        rollback_reason = 'Test data cleanup and schema deprecation'
    WHERE version = '006_esp32_device_schema';
END $$; 