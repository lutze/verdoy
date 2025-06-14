-- Define your production equipment
DO $$
DECLARE
    oven_id UUID;
    sensor_id UUID;
BEGIN
    -- Insert oven if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'DEMO Production Oven #1') THEN
        INSERT INTO entities (id, entity_type, name, properties) VALUES
        (
            uuid_generate_v4(),
            'equipment.oven',
            'DEMO Production Oven #1',
            '{
                "model": "ConvectionPro-5000",
                "serial": "CP5K-2024-001",
                "installDate": "2024-01-15",
                "zones": 3,
                "maxTemp": 350,
                "location": "Production Floor A",
                "manufacturer": "BakeEquip Inc"
            }'
        ) RETURNING id INTO oven_id;
    ELSE
        SELECT id INTO oven_id FROM entities WHERE name = 'DEMO Production Oven #1';
    END IF;

    -- Insert sensor node if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'DEMO ESP32 Node 042') THEN
        INSERT INTO entities (id, entity_type, name, properties) VALUES
        (
            uuid_generate_v4(),
            'sensor.node',
            'DEMO ESP32 Node 042',
            '{
                "macAddress": "24:6F:28:XX:XX:XX",
                "firmware": "LMSevo-v0.4",
                "sensors": ["BME680"],
                "capabilities": ["temperature", "humidity", "pressure", "gas_resistance"],
                "installLocation": "Oven-001-Zone-1"
            }'
        ) RETURNING id INTO sensor_id;
    ELSE
        SELECT id INTO sensor_id FROM entities WHERE name = 'DEMO ESP32 Node 042';
    END IF;

    -- Create relationship if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM relationships 
        WHERE from_entity = sensor_id 
        AND to_entity = oven_id 
        AND relationship_type = 'monitors'
    ) THEN
        INSERT INTO relationships (from_entity, to_entity, relationship_type, properties) VALUES
        (
            sensor_id,
            oven_id,
            'monitors',
            '{
                "zone": 1,
                "position": "upper-center",
                "installDate": "2024-03-01"
            }'
        );
    END IF;
END $$;

-- Define schema for sensor readings
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schemas WHERE id = 'sensor.reading.v1') THEN
        INSERT INTO schemas VALUES
        (
            'sensor.reading.v1',
            1,
            'sensor.reading',
            '{
                "timestamp": {"type": "datetime", "required": true},
                "value": {"type": "number", "required": true},
                "unit": {"type": "string", "required": true},
                "sensorType": {"type": "string", "enum": ["temperature", "humidity", "pressure", "gas_resistance"]},
                "quality": {"type": "string", "enum": ["good", "suspect", "bad"], "default": "good"},
                "calibrationDate": {"type": "datetime"},
                "batteryLevel": {"type": "number", "min": 0, "max": 100}
            }',
            'Initial sensor reading schema',
            NOW(),
            NULL,
            'system'
        );
    END IF;
END $$;

-- Define schema for process parameters
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schemas WHERE id = 'process.baking.v1') THEN
        INSERT INTO schemas VALUES
        (
            'process.baking.v1',
            1,
            'process.baking',
            '{
                "recipe": {"type": "string", "required": true},
                "targetTemp": {"type": "number", "required": true},
                "duration": {"type": "number", "required": true},
                "humidity": {"type": "number"},
                "stages": {"type": "array", "items": {"type": "object"}}
            }',
            'Baking process schema v1',
            NOW(),
            NULL,
            'process-engineer'
        );
    END IF;
END $$;

-- Create a baking process template
DO $$
DECLARE
    process_id UUID;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM processes WHERE name = 'DEMO Sourdough Bread Recipe') THEN
        INSERT INTO processes (id, name, version, process_type, definition) VALUES
        (
            uuid_generate_v4(),
            'DEMO Sourdough Bread Recipe',
            '1.0',
            'baking.bread',
            '{
                "stages": [
                    {
                        "name": "preheat",
                        "duration": 900,
                        "targetTemp": 220,
                        "description": "Preheat oven to target temperature"
                    },
                    {
                        "name": "initial_bake",
                        "duration": 1800,
                        "targetTemp": 220,
                        "steamLevel": "high",
                        "description": "Initial bake with steam"
                    },
                    {
                        "name": "final_bake", 
                        "duration": 1200,
                        "targetTemp": 200,
                        "steamLevel": "none",
                        "description": "Final bake without steam"
                    }
                ],
                "expectedResults": {
                    "internalTemp": 95,
                    "crust": "golden-brown",
                    "totalTime": 3900
                }
            }'
        ) RETURNING id INTO process_id;

        -- Start a process instance
        INSERT INTO process_instances (process_id, batch_id, parameters) VALUES
        (
            process_id,
            'batch-2024-03-19-001',
            '{
                "loafCount": 6,
                "doughWeight": "500g",
                "operator": "baker-jane",
                "startTime": "2024-03-19T08:00:00Z"
            }'
        );
    END IF;
END $$; 