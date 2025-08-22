-- Define sample organizations using pure entity approach
DO $$
DECLARE
    org1_id UUID;
    org2_id UUID;
BEGIN
    -- Insert first organization if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'organization',
            'Acme Research Labs',
            'Leading biotechnology research laboratory',
            '{
                "contact_email": "info@acmeresearch.com",
                "contact_phone": "+1-555-1234",
                "website": "https://acmeresearch.com",
                "address": "123 Science Blvd",
                "city": "Research City",
                "state": "CA",
                "country": "USA",
                "postal_code": "90210",
                "timezone": "America/Los_Angeles",
                "member_count": 25,
                "industry": "biotechnology",
                "founded": "2020-01-01"
            }'::jsonb,
            'active'
        ) RETURNING id INTO org1_id;
    ELSE
        SELECT id INTO org1_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    END IF;

    -- Insert second organization if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'BioTech Innovations' AND entity_type = 'organization') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'organization',
            'BioTech Innovations',
            'Innovative biotech startup focusing on fermentation',
            '{
                "contact_email": "hello@biotechinnovations.com",
                "contact_phone": "+1-555-5678",
                "website": "https://biotechinnovations.com",
                "address": "456 Innovation Drive",
                "city": "Startup City",
                "state": "CA",
                "country": "USA",
                "postal_code": "90211",
                "timezone": "America/Los_Angeles",
                "member_count": 12,
                "industry": "biotechnology",
                "founded": "2022-06-01"
            }'::jsonb,
            'active'
        ) RETURNING id INTO org2_id;
    ELSE
        SELECT id INTO org2_id FROM entities WHERE name = 'BioTech Innovations' AND entity_type = 'organization';
    END IF;
END $$;

-- Define sample projects using pure entity approach
DO $$
DECLARE
    org1_id UUID;
    org2_id UUID;
BEGIN
    -- Get organization IDs
    SELECT id INTO org1_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    SELECT id INTO org2_id FROM entities WHERE name = 'BioTech Innovations' AND entity_type = 'organization';
    
    -- Insert sample projects if they don't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Bioreactor Optimization Study' AND entity_type = 'project') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
        (
            uuid_generate_v4(),
            'project',
            'Bioreactor Optimization Study',
            'Study to optimize bioreactor parameters for maximum yield',
            '{
                "start_date": "2024-01-15",
                "end_date": "2024-06-15",
                "expected_completion": "2024-05-15",
                "actual_completion": null,
                "budget": "$50,000",
                "progress_percentage": 25,
                "project_lead_id": null,
                "priority": "high",
                "tags": ["optimization", "bioreactor", "yield"],
                "project_metadata": {
                    "research_area": "biotechnology",
                    "funding_source": "internal",
                    "team_size": 5
                },
                "settings": {
                    "data_retention_days": 365,
                    "alert_thresholds": {
                        "temperature": {"min": 20, "max": 30},
                        "ph": {"min": 6.5, "max": 7.5}
                    }
                }
            }'::jsonb,
            org1_id,
            'active'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Fermentation Process Development' AND entity_type = 'project') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
        (
            uuid_generate_v4(),
            'project',
            'Fermentation Process Development',
            'Develop new fermentation processes for biofuel production',
            '{
                "start_date": "2024-02-01",
                "end_date": "2024-08-01",
                "expected_completion": "2024-07-15",
                "actual_completion": null,
                "budget": "$75,000",
                "progress_percentage": 40,
                "project_lead_id": null,
                "priority": "medium",
                "tags": ["fermentation", "biofuel", "process-development"],
                "project_metadata": {
                    "research_area": "biofuels",
                    "funding_source": "grant",
                    "team_size": 8
                },
                "settings": {
                    "data_retention_days": 730,
                    "alert_thresholds": {
                        "temperature": {"min": 25, "max": 35},
                        "pressure": {"min": 1.0, "max": 1.2}
                    }
                }
            }'::jsonb,
            org2_id,
            'active'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Sensor Network Deployment' AND entity_type = 'project') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
        (
            uuid_generate_v4(),
            'project',
            'Sensor Network Deployment',
            'Deploy IoT sensor network for environmental monitoring',
            '{
                "start_date": "2024-03-01",
                "end_date": "2024-05-01",
                "expected_completion": "2024-04-30",
                "actual_completion": null,
                "budget": "$25,000",
                "progress_percentage": 60,
                "project_lead_id": null,
                "priority": "low",
                "tags": ["iot", "sensors", "monitoring"],
                "project_metadata": {
                    "research_area": "iot",
                    "funding_source": "internal",
                    "team_size": 3
                },
                "settings": {
                    "data_retention_days": 180,
                    "alert_thresholds": {
                        "temperature": {"min": 15, "max": 25},
                        "humidity": {"min": 40, "max": 60}
                    }
                }
            }'::jsonb,
            org1_id,
            'active'
        );
    END IF;
END $$;

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
            'device.esp32',
            'DEMO ESP32 Node 042',
            '{
                "name": "DEMO ESP32 Node 042",
                "location": "Oven-001-Zone-1",
                "status": "online",
                "firmware": {
                    "version": "LMSevo-v0.4",
                    "lastUpdate": "2024-03-01T00:00:00Z"
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
                        },
                        {
                            "type": "pressure",
                            "unit": "hPa",
                            "range": {
                                "min": 300,
                                "max": 1100
                            }
                        },
                        {
                            "type": "gas_resistance",
                            "unit": "kOhm",
                            "range": {
                                "min": 0,
                                "max": 100000
                            }
                        }
                    ]
                },
                "config": {
                    "readingInterval": 300,
                    "wifi": {
                        "ssid": "Production-Network",
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
                    "installDate": "2024-03-01",
                    "position": "upper-center",
                    "zone": 1
                }
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