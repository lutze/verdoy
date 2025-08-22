-- =====================================================================
-- Database Test Data Migration: Sample data for development and testing
-- =====================================================================
-- This migration populates the database with test organizations, users,
-- projects, devices, processes, and experiments for development and testing.
-- This script should only be run after 001_schema.sql
-- =====================================================================

-- =====================================================================
-- ORGANIZATIONS
-- =====================================================================

-- Define sample organizations using pure entity approach
DO $$
DECLARE
    org1_id UUID;
    org2_id UUID;
    default_org_id UUID;
BEGIN
    -- Create default organization
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Default Organization' AND entity_type = 'organization') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'organization',
            'Default Organization',
            'Default organization for existing entities',
            '{
                "name": "Default Organization",
                "description": "Default organization for existing entities",
                "contact_email": "admin@default.org",
                "contact_phone": "+1-555-0000",
                "website": "https://default.org",
                "address": "123 Default St",
                "city": "Default City",
                "state": "Default State",
                "country": "Default Country",
                "postal_code": "12345",
                "timezone": "UTC",
                "member_count": 0
            }',
            'active'
        ) RETURNING id INTO default_org_id;
    ELSE
        SELECT id INTO default_org_id FROM entities WHERE name = 'Default Organization' AND entity_type = 'organization';
    END IF;

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

-- =====================================================================
-- USERS
-- =====================================================================

-- Create test users
DO $$
DECLARE
    default_org_id UUID;
    org1_id UUID;
    org2_id UUID;
    test_user_id UUID;
    user1_id UUID;
    user2_id UUID;
    user3_id UUID;
BEGIN
    -- Get organization IDs
    SELECT id INTO default_org_id FROM entities WHERE name = 'Default Organization' AND entity_type = 'organization';
    SELECT id INTO org1_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    SELECT id INTO org2_id FROM entities WHERE name = 'BioTech Innovations' AND entity_type = 'organization';
    
    -- Create default test user
    IF NOT EXISTS (SELECT 1 FROM entities WHERE entity_type = 'user' AND properties->>'email' = 'test@example.com') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status, is_active) VALUES
        (
            uuid_generate_v4(),
            'user',
            'Test User',
            'Default test user for development and testing',
            '{
                "email": "test@example.com",
                "hashed_password": "$2b$12$2KKaRCpDxQcm2p99qfGoCerZaHWaNd3/cKiT7QvsyNQ.jslRWV5da",
                "is_superuser": false,
                "user_type": "standard",
                "role": "admin",
                "department": "Development",
                "created_by": "system"
            }',
            default_org_id,
            'active',
            true
        ) RETURNING id INTO test_user_id;
    END IF;

    -- Insert Dr. Sarah Johnson
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Dr. Sarah Johnson' AND entity_type = 'user') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'user',
            'Dr. Sarah Johnson',
            'Lead Research Scientist at Acme Research Labs',
            '{
                "email": "sarah.johnson@acmeresearch.com",
                "hashed_password": "$2b$12$2KKaRCpDxQcm2p99qfGoCerZaHWaNd3/cKiT7QvsyNQ.jslRWV5da",
                "is_superuser": false,
                "is_admin": true,
                "title": "Lead Research Scientist",
                "department": "Research & Development",
                "phone": "+1-555-1001",
                "timezone": "America/Los_Angeles"
            }'::jsonb,
            'active'
        ) RETURNING id INTO user1_id;
    ELSE
        SELECT id INTO user1_id FROM entities WHERE name = 'Dr. Sarah Johnson' AND entity_type = 'user';
    END IF;

    -- Insert Dr. Michael Chen
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Dr. Michael Chen' AND entity_type = 'user') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'user',
            'Dr. Michael Chen',
            'Chief Technology Officer at BioTech Innovations',
            '{
                "email": "michael.chen@biotechinnovations.com",
                "hashed_password": "$2b$12$2KKaRCpDxQcm2p99qfGoCerZaHWaNd3/cKiT7QvsyNQ.jslRWV5da",
                "is_superuser": false,
                "is_admin": true,
                "title": "Chief Technology Officer",
                "department": "Technology",
                "phone": "+1-555-2002",
                "timezone": "America/Los_Angeles"
            }'::jsonb,
            'active'
        ) RETURNING id INTO user2_id;
    ELSE
        SELECT id INTO user2_id FROM entities WHERE name = 'Dr. Michael Chen' AND entity_type = 'user';
    END IF;

    -- Insert Alex Rodriguez
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Alex Rodriguez' AND entity_type = 'user') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
        (
            uuid_generate_v4(),
            'user',
            'Alex Rodriguez',
            'Research Assistant at Acme Research Labs',
            '{
                "email": "alex.rodriguez@acmeresearch.com",
                "hashed_password": "$2b$12$2KKaRCpDxQcm2p99qfGoCerZaHWaNd3/cKiT7QvsyNQ.jslRWV5da",
                "is_superuser": false,
                "is_admin": false,
                "title": "Research Assistant",
                "department": "Research & Development",
                "phone": "+1-555-1003",
                "timezone": "America/Los_Angeles"
            }'::jsonb,
            'active'
        ) RETURNING id INTO user3_id;
    ELSE
        SELECT id INTO user3_id FROM entities WHERE name = 'Alex Rodriguez' AND entity_type = 'user';
    END IF;

    -- Add users to organizations as members
    -- Dr. Sarah Johnson as admin of Acme Research Labs
    IF NOT EXISTS (SELECT 1 FROM organization_members WHERE organization_id = org1_id AND user_id = user1_id) THEN
        INSERT INTO organization_members (organization_id, user_id, role, is_active, joined_at) VALUES
        (org1_id, user1_id, 'admin', true, NOW());
    END IF;

    -- Dr. Michael Chen as admin of BioTech Innovations
    IF NOT EXISTS (SELECT 1 FROM organization_members WHERE organization_id = org2_id AND user_id = user2_id) THEN
        INSERT INTO organization_members (organization_id, user_id, role, is_active, joined_at) VALUES
        (org2_id, user2_id, 'admin', true, NOW());
    END IF;

    -- Alex Rodriguez as member of Acme Research Labs
    IF NOT EXISTS (SELECT 1 FROM organization_members WHERE organization_id = org1_id AND user_id = user3_id) THEN
        INSERT INTO organization_members (organization_id, user_id, role, is_active, joined_at) VALUES
        (org1_id, user3_id, 'member', true, NOW());
    END IF;
END $$;

-- =====================================================================
-- PROJECTS
-- =====================================================================

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

-- =====================================================================
-- DEVICES
-- =====================================================================

-- Define production equipment and devices
DO $$
DECLARE
    oven_id UUID;
    sensor_id UUID;
    acme_org_id UUID;
BEGIN
    -- Get Acme organization ID
    SELECT id INTO acme_org_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';

    -- Insert oven if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'DEMO Production Oven #1') THEN
        INSERT INTO entities (id, entity_type, name, properties, organization_id) VALUES
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
            }',
            acme_org_id
        ) RETURNING id INTO oven_id;
    ELSE
        SELECT id INTO oven_id FROM entities WHERE name = 'DEMO Production Oven #1';
    END IF;

    -- Insert ESP32 sensor node if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'DEMO ESP32 Node 042') THEN
        INSERT INTO entities (id, entity_type, name, properties, organization_id) VALUES
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
            }',
            acme_org_id
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

-- =====================================================================
-- SCHEMAS
-- =====================================================================

-- Define schema for ESP32 devices
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

-- =====================================================================
-- PROCESSES
-- =====================================================================

-- Create process templates
DO $$
DECLARE
    process_id UUID;
    acme_org_id UUID;
BEGIN
    -- Get Acme organization ID
    SELECT id INTO acme_org_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';

    -- Create baking process template
    IF NOT EXISTS (SELECT 1 FROM processes WHERE name = 'DEMO Sourdough Bread Recipe') THEN
        INSERT INTO processes (id, name, version, process_type, definition, organization_id, description, is_template) VALUES
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
            }',
            acme_org_id,
            'Demo sourdough bread baking process',
            true
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

    -- Create fermentation process
    IF NOT EXISTS (SELECT 1 FROM processes WHERE name = 'Acme Fermentation Protocol v1.0') THEN
        INSERT INTO processes (id, name, version, process_type, definition, organization_id, description, is_template) VALUES
        (
            uuid_generate_v4(),
            'Acme Fermentation Protocol v1.0',
            '1.0',
            'fermentation',
            '{
                "stages": [
                    {
                        "name": "inoculation",
                        "duration": 3600,
                        "targetTemp": 25.0,
                        "targetPh": 7.0,
                        "targetDo": 80.0,
                        "description": "Inoculate bioreactor with starter culture"
                    },
                    {
                        "name": "lag_phase",
                        "duration": 7200,
                        "targetTemp": 25.0,
                        "targetPh": 7.0,
                        "targetDo": 80.0,
                        "description": "Lag phase - culture adaptation"
                    },
                    {
                        "name": "exponential_growth",
                        "duration": 14400,
                        "targetTemp": 25.0,
                        "targetPh": 6.8,
                        "targetDo": 60.0,
                        "description": "Exponential growth phase"
                    },
                    {
                        "name": "stationary_phase",
                        "duration": 7200,
                        "targetTemp": 25.0,
                        "targetPh": 6.5,
                        "targetDo": 40.0,
                        "description": "Stationary phase - product formation"
                    },
                    {
                        "name": "harvest",
                        "duration": 1800,
                        "targetTemp": 25.0,
                        "targetPh": 6.5,
                        "targetDo": 40.0,
                        "description": "Harvest phase - collect product"
                    }
                ],
                "expectedResults": {
                    "finalBiomass": "15-20 g/L",
                    "productTiter": "5-8 g/L",
                    "totalTime": 34200,
                    "yield": "0.3-0.4 g/g"
                },
                "safetyParameters": {
                    "maxTemp": 30.0,
                    "minTemp": 20.0,
                    "maxPh": 8.0,
                    "minPh": 6.0,
                    "maxPressure": 1.5,
                    "minDo": 20.0
                }
            }',
            acme_org_id,
            'Standard fermentation protocol for recombinant protein production',
            true
        );
    END IF;
END $$;

-- =====================================================================
-- BIOREACTORS AND EXPERIMENTS
-- =====================================================================

-- Add demo data for Acme Research Labs
DO $$
DECLARE
    acme_org_id UUID;
    demo_process_id UUID;
    demo_bioreactor_id UUID;
    demo_experiment_id UUID;
    demo_project_id UUID;
    sarah_user_id UUID;
BEGIN
    -- Get organization and user IDs
    SELECT id INTO acme_org_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    SELECT id INTO demo_project_id FROM entities WHERE name = 'Bioreactor Optimization Study' AND entity_type = 'project';
    SELECT id INTO demo_process_id FROM processes WHERE name = 'Acme Fermentation Protocol v1.0';
    SELECT id INTO sarah_user_id FROM entities WHERE name = 'Dr. Sarah Johnson' AND entity_type = 'user';
    
    -- Create demo bioreactor
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Acme Bioreactor BR-001' AND entity_type = 'device.bioreactor') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
        (
            uuid_generate_v4(),
            'device.bioreactor',
            'Acme Bioreactor BR-001',
            '5L benchtop bioreactor for fermentation studies',
            '{
                "model": "BioFlo 310",
                "manufacturer": "Eppendorf",
                "serial_number": "BF310-2024-001",
                "vessel_volume": 5.0,
                "working_volume": 3.0,
                "sensors": [
                    {
                        "type": "temperature",
                        "range": [0, 50],
                        "accuracy": 0.1,
                        "unit": "°C"
                    },
                    {
                        "type": "ph",
                        "range": [0, 14],
                        "accuracy": 0.01,
                        "unit": "pH"
                    },
                    {
                        "type": "dissolved_oxygen",
                        "range": [0, 100],
                        "accuracy": 1.0,
                        "unit": "%"
                    },
                    {
                        "type": "pressure",
                        "range": [0, 2],
                        "accuracy": 0.01,
                        "unit": "bar"
                    }
                ],
                "actuators": [
                    {
                        "type": "heating",
                        "power": 500,
                        "unit": "W"
                    },
                    {
                        "type": "cooling",
                        "power": 300,
                        "unit": "W"
                    },
                    {
                        "type": "agitation",
                        "range": [0, 1200],
                        "unit": "rpm"
                    },
                    {
                        "type": "aeration",
                        "range": [0, 2],
                        "unit": "vvm"
                    }
                ],
                "location": "Lab A - Bench 3",
                "installation_date": "2024-01-15",
                "last_calibration": "2024-03-01",
                "next_calibration": "2024-06-01",
                "status": "available"
            }'::jsonb,
            acme_org_id,
            'active'
        ) RETURNING id INTO demo_bioreactor_id;
    ELSE
        SELECT id INTO demo_bioreactor_id FROM entities WHERE name = 'Acme Bioreactor BR-001' AND entity_type = 'device.bioreactor';
    END IF;

    -- Create demo experiment
    IF NOT EXISTS (SELECT 1 FROM entities WHERE name = 'Recombinant Protein Production Study' AND entity_type = 'experiment') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
        (
            uuid_generate_v4(),
            'experiment',
            'Recombinant Protein Production Study',
            'Study to optimize recombinant protein production using E. coli fermentation',
            ('{
                "project_id": "' || demo_project_id || '",
                "process_id": "' || demo_process_id || '",
                "bioreactor_id": "' || demo_bioreactor_id || '",
                "status": "active",
                "current_trial": 2,
                "total_trials": 3,
                "parameters": {
                    "strain": "E. coli BL21(DE3)",
                    "plasmid": "pET28a-GFP",
                    "media": "TB",
                    "induction_time": 4,
                    "induction_od": 0.6,
                    "iptg_concentration": 1.0
                },
                "metadata": {
                    "objective": "Optimize recombinant GFP production",
                    "hypothesis": "Higher induction OD will increase protein yield",
                    "expected_outcomes": [
                        "GFP titer > 5 g/L",
                        "Process time < 24 hours",
                        "Yield > 0.3 g/g"
                    ],
                    "tags": ["fermentation", "recombinant-protein", "optimization"],
                    "safety_notes": "Standard BSL-1 containment required"
                },
                "started_at": null,
                "completed_at": null,
                "duration_minutes": null,
                "results": {},
                "error_message": null,
                "progress_percentage": 0,
                "is_running": true,
                "is_finished": false,
                "can_start": false,
                "can_pause": true,
                "can_resume": false,
                "can_stop": true
            }')::jsonb,
            acme_org_id,
            'active'
        ) RETURNING id INTO demo_experiment_id;
    ELSE
        SELECT id INTO demo_experiment_id FROM entities WHERE name = 'Recombinant Protein Production Study' AND entity_type = 'experiment';
    END IF;

    -- Create experiment trials
    IF NOT EXISTS (SELECT 1 FROM experiment_trials WHERE experiment_id = demo_experiment_id AND trial_number = 1) THEN
        INSERT INTO experiment_trials (id, experiment_id, trial_number, status, started_at, completed_at, parameters, results, created_by) VALUES
        (
            uuid_generate_v4(),
            demo_experiment_id,
            1,
            'completed',
            NOW() - INTERVAL '2 days',
            NOW() - INTERVAL '1 day',
            '{
                "strain": "E. coli BL21(DE3)",
                "plasmid": "pET28a-GFP",
                "media": "TB",
                "induction_time": 4,
                "induction_od": 0.6,
                "iptg_concentration": 1.0,
                "initial_od": 0.1,
                "temperature": 25.0,
                "ph": 7.0,
                "agitation": 800,
                "aeration": 1.0
            }',
            '{
                "final_od": 15.2,
                "final_ph": 6.8,
                "gfp_titer": 4.8,
                "yield": 0.32,
                "process_time": 22.5,
                "notes": "Good growth observed, slightly lower than target titer"
            }',
            sarah_user_id
        );
    END IF;

    -- Create a second trial (running)
    IF NOT EXISTS (SELECT 1 FROM experiment_trials WHERE experiment_id = demo_experiment_id AND trial_number = 2) THEN
        INSERT INTO experiment_trials (id, experiment_id, trial_number, status, started_at, completed_at, parameters, results, created_by) VALUES
        (
            uuid_generate_v4(),
            demo_experiment_id,
            2,
            'running',
            NOW() - INTERVAL '6 hours',
            null,
            '{
                "strain": "E. coli BL21(DE3)",
                "plasmid": "pET28a-GFP",
                "media": "TB",
                "induction_time": 4,
                "induction_od": 0.8,
                "iptg_concentration": 1.0,
                "initial_od": 0.1,
                "temperature": 25.0,
                "ph": 7.0,
                "agitation": 800,
                "aeration": 1.0
            }',
            '{
                "current_od": 0.45,
                "current_ph": 7.1,
                "current_temperature": 25.2,
                "current_do": 75.0,
                "stage": "lag_phase",
                "time_elapsed": 21600
            }',
            sarah_user_id
        );
    END IF;
END $$;

-- =====================================================================
-- SAMPLE EVENTS
-- =====================================================================

-- Create some sample events for testing
DO $$
DECLARE
    oven_id UUID;
    sensor_id UUID;
    test_device_id UUID;
BEGIN
    -- Get device IDs
    SELECT id INTO oven_id FROM entities WHERE name = 'DEMO Production Oven #1';
    SELECT id INTO sensor_id FROM entities WHERE name = 'DEMO ESP32 Node 042';
    
    -- Create events for device creation
    IF oven_id IS NOT NULL THEN
        INSERT INTO events (event_type, entity_id, entity_type, data) VALUES
        (
            'equipment.created',
            oven_id,
            'equipment.oven',
            '{
                "name": "DEMO Production Oven #1",
                "created_by": "system"
            }'
        );
    END IF;

    IF sensor_id IS NOT NULL THEN
        INSERT INTO events (event_type, entity_id, entity_type, data) VALUES
        (
            'device.created',
            sensor_id,
            'device.esp32',
            '{
                "name": "DEMO ESP32 Node 042",
                "created_by": "system"
            }'
        );
    END IF;
END $$;

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('002_test_data') ON CONFLICT (version) DO NOTHING;
