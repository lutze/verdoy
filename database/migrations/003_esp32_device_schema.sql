-- Migration: Add ESP32 device schema
-- Description: Defines the schema for ESP32 devices and their properties

-- Add ESP32 device schema
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schemas WHERE id = 'device.esp32.v1') THEN
        INSERT INTO schemas VALUES
        (
            'device.esp32.v1',
            1,
            'device.esp32',
            '{
                "name": {"type": "string", "required": true},
                "location": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["online", "offline", "maintenance", "error"],
                    "default": "offline"
                },
                "firmware": {
                    "version": {"type": "string", "required": true},
                    "lastUpdate": {"type": "datetime"}
                },
                "hardware": {
                    "model": {"type": "string", "required": true},
                    "macAddress": {"type": "string", "required": true},
                    "sensors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "required": true},
                                "unit": {"type": "string", "required": true},
                                "range": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "config": {
                    "readingInterval": {"type": "integer", "default": 300},
                    "wifi": {
                        "ssid": {"type": "string"},
                        "signalStrength": {"type": "integer"}
                    },
                    "alertThresholds": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"}
                            }
                        }
                    }
                },
                "lastSeen": {"type": "datetime"},
                "batteryLevel": {"type": "number", "min": 0, "max": 100},
                "metadata": {
                    "type": "object",
                    "additionalProperties": true
                }
            }',
            'ESP32 device schema v1',
            NOW(),
            NULL,
            'system'
        );
    END IF;
END $$;

-- Add a test device to verify schema
DO $$
DECLARE
    device_id UUID;
BEGIN
    -- Create a test ESP32 device
    INSERT INTO entities (id, entity_type, name, properties) VALUES
    (
        uuid_generate_v4(),
        'device.esp32',
        'Test ESP32 Device',
        '{
            "name": "Test ESP32 Device",
            "location": "Test Lab",
            "status": "online",
            "firmware": {
                "version": "1.0.0",
                "lastUpdate": "2024-03-20T10:00:00Z"
            },
            "hardware": {
                "model": "ESP32-WROOM-32",
                "macAddress": "24:6F:28:XX:XX:XX",
                "sensors": [
                    {
                        "type": "temperature",
                        "unit": "celsius",
                        "range": {
                            "min": -40,
                            "max": 125
                        }
                    },
                    {
                        "type": "humidity",
                        "unit": "percent",
                        "range": {
                            "min": 0,
                            "max": 100
                        }
                    }
                ]
            },
            "config": {
                "readingInterval": 300,
                "wifi": {
                    "ssid": "TestNetwork",
                    "signalStrength": -65
                },
                "alertThresholds": {
                    "temperature": {
                        "min": 15,
                        "max": 30
                    },
                    "humidity": {
                        "min": 30,
                        "max": 70
                    }
                }
            },
            "lastSeen": "2024-03-20T10:00:00Z",
            "batteryLevel": 85,
            "metadata": {
                "notes": "Test device for schema validation"
            }
        }'
    ) RETURNING id INTO device_id;

    -- Create an event for device creation
    INSERT INTO events (event_type, entity_id, entity_type, data) VALUES
    (
        'device.created',
        device_id,
        'device.esp32',
        '{
            "name": "Test ESP32 Device",
            "created_by": "system"
        }'
    );
END $$;

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('006_esp32_device_schema'); 