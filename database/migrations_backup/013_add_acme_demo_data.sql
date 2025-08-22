-- Migration: Add demo data for Acme Research Labs
-- This migration adds a demo Process, Bioreactor, and Experiment for Acme Research Labs

-- Add demo fermentation process for Acme Research Labs
DO $$
DECLARE
    acme_org_id UUID;
    demo_process_id UUID;
    demo_bioreactor_id UUID;
    demo_experiment_id UUID;
    demo_project_id UUID;
BEGIN
    -- Get Acme Research Labs organization ID
    SELECT id INTO acme_org_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    
    -- Get the Bioreactor Optimization Study project
    SELECT id INTO demo_project_id FROM entities WHERE name = 'Bioreactor Optimization Study' AND entity_type = 'project';
    
    -- Create demo fermentation process
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
        ) RETURNING id INTO demo_process_id;
    ELSE
        SELECT id INTO demo_process_id FROM processes WHERE name = 'Acme Fermentation Protocol v1.0';
    END IF;

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
                "status": "draft",
                "current_trial": 0,
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
                "is_running": false,
                "is_finished": false,
                "can_start": true,
                "can_pause": false,
                "can_resume": false,
                "can_stop": false
            }')::jsonb,
            acme_org_id,
            'active'
        ) RETURNING id INTO demo_experiment_id;
    END IF;

    -- Create a demo experiment trial
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
            (SELECT id FROM entities WHERE name = 'Dr. Sarah Johnson' AND entity_type = 'user' LIMIT 1)
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
            (SELECT id FROM entities WHERE name = 'Dr. Sarah Johnson' AND entity_type = 'user' LIMIT 1)
        );
    END IF;

    -- Update the experiment to reflect the current trial
    UPDATE entities 
    SET properties = jsonb_set(
        properties, 
        '{current_trial}', 
        '2'
    )
    WHERE id = demo_experiment_id;

    -- Update the experiment status to reflect running trial
    UPDATE entities 
    SET properties = jsonb_set(
        properties, 
        '{status,is_running,can_start,can_pause,can_resume,can_stop}', 
        '["active", true, false, true, false, true]'
    )
    WHERE id = demo_experiment_id;

    RAISE NOTICE 'Demo data created for Acme Research Labs: Process %, Bioreactor %, Experiment %', 
        demo_process_id, demo_bioreactor_id, demo_experiment_id;

END $$;
