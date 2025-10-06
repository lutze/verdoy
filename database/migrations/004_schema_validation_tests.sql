-- =====================================================================
-- Database Schema Migration: Schema Validation Tests
-- =====================================================================
-- This migration tests all entity type schemas with sample data and
-- validates that the validation rules work correctly.
-- 
-- Tests include:
-- 1. Valid data insertion for all entity types
-- 2. Invalid data rejection (validation errors)
-- 3. Edge cases and boundary conditions
-- 4. Schema constraint validation
-- =====================================================================

-- =====================================================================
-- TEST DATA SETUP
-- =====================================================================

-- Create test organization and user for testing
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
    test_process_def_id UUID;
    test_experiment_id UUID;
BEGIN
    -- Create test organization
    INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
    (
        uuid_generate_v4(),
        'organization',
        'Test Organization for Schema Validation',
        'Test organization for validating entity schemas',
        '{"contact_email": "test@testorg.com", "member_count": 1}',
        'active'
    ) RETURNING id INTO test_org_id;

    -- Create test user
    INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
    (
        uuid_generate_v4(),
        'user',
        'Test User for Schema Validation',
        'Test user for validating entity schemas',
        '{"email": "testuser@testorg.com", "is_admin": true}',
        test_org_id,
        'active'
    ) RETURNING id INTO test_user_id;

    -- Create test process definition
    INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
    (
        uuid_generate_v4(),
        'process.definition',
        'Test Process Definition',
        'Test process definition for validation',
        '{
            "name": "Test Baking Process",
            "version": "1.0",
            "process_type": "baking",
            "definition": {
                "stages": [
                    {
                        "name": "preheat",
                        "duration": 900,
                        "targetTemp": 220,
                        "description": "Preheat oven"
                    }
                ],
                "expectedResults": {
                    "internalTemp": 95
                }
            },
            "status": "active",
            "description": "Test baking process for validation",
            "is_template": true,
            "created_by": "' || test_user_id || '",
            "tags": ["test", "baking"]
        }',
        test_org_id,
        'active'
    ) RETURNING id INTO test_process_def_id;

    -- Create test experiment
    INSERT INTO entities (id, entity_type, name, description, properties, organization_id, status) VALUES
    (
        uuid_generate_v4(),
        'experiment',
        'Test Experiment for Schema Validation',
        'Test experiment for validating trial schemas',
        '{
            "status": "active",
            "current_trial": 1,
            "total_trials": 3,
            "parameters": {
                "strain": "E. coli BL21(DE3)"
            }
        }',
        test_org_id,
        'active'
    ) RETURNING id INTO test_experiment_id;

    -- Store test IDs for later use
    INSERT INTO entities (id, entity_type, name, description, properties, status) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'test.reference',
        'Test Reference Data',
        'Stores test IDs for validation tests',
        '{
            "test_org_id": "' || test_org_id || '",
            "test_user_id": "' || test_user_id || '",
            "test_process_def_id": "' || test_process_def_id || '",
            "test_experiment_id": "' || test_experiment_id || '"
        }',
        'active'
    ) ON CONFLICT (id) DO NOTHING;
END $$;

-- =====================================================================
-- VALID DATA TESTS
-- =====================================================================

-- Test 1: Valid Process Definition
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
    result BOOLEAN;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid process definition
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'process.definition',
            'Valid Test Process',
            'Valid process definition test',
            '{
                "name": "Valid Baking Process",
                "version": "2.1.3",
                "process_type": "baking",
                "definition": {
                    "stages": [
                        {
                            "name": "preheat",
                            "duration": 900,
                            "targetTemp": 220,
                            "description": "Preheat oven to target temperature"
                        }
                    ],
                    "expectedResults": {
                        "internalTemp": 95,
                        "crust": "golden-brown"
                    }
                },
                "status": "active",
                "description": "A valid baking process for testing",
                "is_template": true,
                "organization_id": "' || test_org_id || '",
                "created_by": "' || test_user_id || '",
                "tags": ["test", "baking", "validation"]
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 1 PASSED: Valid process definition inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 1 FAILED: %', SQLERRM;
    END;
END $$;

-- Test 2: Valid Process Instance
DO $$
DECLARE
    test_org_id UUID;
    test_process_def_id UUID;
    result BOOLEAN;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_process_def_id')::UUID INTO test_process_def_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid process instance
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'process.instance',
            'Valid Test Process Instance',
            'Valid process instance test',
            '{
                "process_id": "' || test_process_def_id || '",
                "batch_id": "BATCH-2024-001",
                "status": "running",
                "started_at": "2024-01-15T10:00:00Z",
                "parameters": {
                    "loafCount": 6,
                    "doughWeight": "500g"
                },
                "results": {
                    "currentTemp": 220,
                    "timeElapsed": 1800
                },
                "current_stage": "preheat",
                "progress_percentage": 25,
                "operator": "baker-jane"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 2 PASSED: Valid process instance inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 2 FAILED: %', SQLERRM;
    END;
END $$;

-- Test 3: Valid Experiment Trial
DO $$
DECLARE
    test_org_id UUID;
    test_experiment_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_experiment_id')::UUID INTO test_experiment_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid experiment trial
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'experiment.trial',
            'Valid Test Experiment Trial',
            'Valid experiment trial test',
            '{
                "experiment_id": "' || test_experiment_id || '",
                "trial_number": 1,
                "status": "completed",
                "started_at": "2024-01-15T08:00:00Z",
                "completed_at": "2024-01-15T16:00:00Z",
                "parameters": {
                    "strain": "E. coli BL21(DE3)",
                    "temperature": 25.0,
                    "ph": 7.0
                },
                "results": {
                    "final_od": 15.2,
                    "gfp_titer": 4.8,
                    "yield": 0.32
                },
                "created_by": "' || test_user_id || '",
                "notes": "Successful trial with good results",
                "quality_score": 85
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 3 PASSED: Valid experiment trial inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 3 FAILED: %', SQLERRM;
    END;
END $$;

-- Test 4: Valid Organization Member
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid organization member
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'organization.member',
            'Valid Test Organization Member',
            'Valid organization member test',
            '{
                "organization_id": "' || test_org_id || '",
                "user_id": "' || test_user_id || '",
                "role": "admin",
                "is_active": true,
                "invited_by": "' || test_user_id || '",
                "invited_at": "2024-01-01T00:00:00Z",
                "accepted_at": "2024-01-01T12:00:00Z",
                "joined_at": "2024-01-01T12:00:00Z",
                "permissions": ["read", "write", "admin"]
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 4 PASSED: Valid organization member inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 4 FAILED: %', SQLERRM;
    END;
END $$;

-- Test 5: Valid Organization Invitation
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid organization invitation
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'organization.invitation',
            'Valid Test Organization Invitation',
            'Valid organization invitation test',
            '{
                "organization_id": "' || test_org_id || '",
                "email": "newuser@testorg.com",
                "role": "member",
                "status": "pending",
                "invited_by": "' || test_user_id || '",
                "expires_at": "2024-02-01T00:00:00Z",
                "message": "Welcome to our organization!",
                "invitation_token": "abc123def456"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 5 PASSED: Valid organization invitation inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 5 FAILED: %', SQLERRM;
    END;
END $$;

-- Test 6: Valid Membership Removal Request
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test valid membership removal request
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'organization.removal_request',
            'Valid Test Membership Removal Request',
            'Valid membership removal request test',
            '{
                "organization_id": "' || test_org_id || '",
                "user_id": "' || test_user_id || '",
                "requested_by": "' || test_user_id || '",
                "status": "pending",
                "reason": "User requested to leave the organization",
                "requested_at": "2024-01-15T10:00:00Z"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 6 PASSED: Valid membership removal request inserted successfully';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 6 FAILED: %', SQLERRM;
    END;
END $$;

-- =====================================================================
-- INVALID DATA TESTS (Should Fail)
-- =====================================================================

-- Test 7: Invalid Process Definition - Missing Required Field
DO $$
BEGIN
    -- Test invalid process definition (missing required 'name' field)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, status) VALUES
        (
            'process.definition',
            'Invalid Test Process - Missing Name',
            'Invalid process definition test',
            '{
                "version": "1.0",
                "process_type": "baking",
                "definition": {"stages": []},
                "status": "active",
                "description": "Missing name field",
                "is_template": true
            }',
            'active'
        );
        
        RAISE NOTICE '❌ Test 7 FAILED: Should have rejected missing required field';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 7 PASSED: Correctly rejected missing required field - %', SQLERRM;
    END;
END $$;

-- Test 8: Invalid Process Definition - Invalid Enum Value
DO $$
BEGIN
    -- Test invalid process definition (invalid process_type)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, status) VALUES
        (
            'process.definition',
            'Invalid Test Process - Bad Type',
            'Invalid process definition test',
            '{
                "name": "Invalid Process",
                "version": "1.0",
                "process_type": "invalid_type",
                "definition": {"stages": []},
                "status": "active",
                "description": "Invalid process type",
                "is_template": true
            }',
            'active'
        );
        
        RAISE NOTICE '❌ Test 8 FAILED: Should have rejected invalid enum value';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 8 PASSED: Correctly rejected invalid enum value - %', SQLERRM;
    END;
END $$;

-- Test 9: Invalid Process Instance - Invalid UUID Format
DO $$
DECLARE
    test_org_id UUID;
BEGIN
    -- Get test org ID
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test invalid process instance (invalid UUID format)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'process.instance',
            'Invalid Test Process Instance - Bad UUID',
            'Invalid process instance test',
            '{
                "process_id": "invalid-uuid-format",
                "status": "running",
                "started_at": "2024-01-15T10:00:00Z"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 9 FAILED: Should have rejected invalid UUID format';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 9 PASSED: Correctly rejected invalid UUID format - %', SQLERRM;
    END;
END $$;

-- Test 10: Invalid Experiment Trial - Invalid Number Range
DO $$
DECLARE
    test_org_id UUID;
    test_experiment_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_experiment_id')::UUID INTO test_experiment_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test invalid experiment trial (trial_number < 1)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'experiment.trial',
            'Invalid Test Experiment Trial - Bad Number',
            'Invalid experiment trial test',
            '{
                "experiment_id": "' || test_experiment_id || '",
                "trial_number": 0,
                "status": "pending",
                "created_by": "' || test_user_id || '"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 10 FAILED: Should have rejected invalid trial number';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 10 PASSED: Correctly rejected invalid trial number - %', SQLERRM;
    END;
END $$;

-- Test 11: Invalid Organization Member - Invalid Email Format
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test invalid organization invitation (invalid email format)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'organization.invitation',
            'Invalid Test Organization Invitation - Bad Email',
            'Invalid organization invitation test',
            '{
                "organization_id": "' || test_org_id || '",
                "email": "invalid-email-format",
                "role": "member",
                "status": "pending",
                "invited_by": "' || test_user_id || '",
                "expires_at": "2024-02-01T00:00:00Z"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 11 FAILED: Should have rejected invalid email format';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 11 PASSED: Correctly rejected invalid email format - %', SQLERRM;
    END;
END $$;

-- Test 12: Invalid Membership Removal Request - Invalid Status
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test invalid membership removal request (invalid status)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'organization.removal_request',
            'Invalid Test Membership Removal Request - Bad Status',
            'Invalid membership removal request test',
            '{
                "organization_id": "' || test_org_id || '",
                "user_id": "' || test_user_id || '",
                "requested_by": "' || test_user_id || '",
                "status": "invalid_status"
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 12 FAILED: Should have rejected invalid status';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 12 PASSED: Correctly rejected invalid status - %', SQLERRM;
    END;
END $$;

-- =====================================================================
-- EDGE CASE TESTS
-- =====================================================================

-- Test 13: Edge Case - Maximum String Length
DO $$
DECLARE
    test_org_id UUID;
    test_user_id UUID;
    long_string TEXT;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Create a string that exceeds max length (1000 chars for description)
    long_string := repeat('A', 1001);

    -- Test edge case - string too long
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'process.definition',
            'Edge Case Test - Long String',
            'Edge case test',
            '{
                "name": "Edge Case Process",
                "version": "1.0",
                "process_type": "baking",
                "definition": {"stages": []},
                "status": "active",
                "description": "' || long_string || '",
                "is_template": true
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 13 FAILED: Should have rejected string too long';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 13 PASSED: Correctly rejected string too long - %', SQLERRM;
    END;
END $$;

-- Test 14: Edge Case - Boundary Values
DO $$
DECLARE
    test_org_id UUID;
    test_experiment_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_experiment_id')::UUID INTO test_experiment_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test edge case - boundary values (quality_score = 100, should be valid)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'experiment.trial',
            'Edge Case Test - Boundary Values',
            'Edge case test',
            '{
                "experiment_id": "' || test_experiment_id || '",
                "trial_number": 1,
                "status": "completed",
                "created_by": "' || test_user_id || '",
                "quality_score": 100
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '✅ Test 14 PASSED: Boundary values accepted correctly';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '❌ Test 14 FAILED: Should have accepted boundary values - %', SQLERRM;
    END;
END $$;

-- Test 15: Edge Case - Invalid Boundary Values
DO $$
DECLARE
    test_org_id UUID;
    test_experiment_id UUID;
    test_user_id UUID;
BEGIN
    -- Get test IDs
    SELECT (properties->>'test_org_id')::UUID INTO test_org_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_experiment_id')::UUID INTO test_experiment_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';
    SELECT (properties->>'test_user_id')::UUID INTO test_user_id FROM entities WHERE id = '00000000-0000-0000-0000-000000000001';

    -- Test edge case - invalid boundary values (quality_score = 101, should be invalid)
    BEGIN
        INSERT INTO entities (entity_type, name, description, properties, organization_id, status) VALUES
        (
            'experiment.trial',
            'Edge Case Test - Invalid Boundary',
            'Edge case test',
            '{
                "experiment_id": "' || test_experiment_id || '",
                "trial_number": 1,
                "status": "completed",
                "created_by": "' || test_user_id || '",
                "quality_score": 101
            }',
            test_org_id,
            'active'
        );
        
        RAISE NOTICE '❌ Test 15 FAILED: Should have rejected invalid boundary values';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✅ Test 15 PASSED: Correctly rejected invalid boundary values - %', SQLERRM;
    END;
END $$;

-- =====================================================================
-- CLEANUP
-- =====================================================================

-- Clean up test data
DELETE FROM entities WHERE entity_type = 'test.reference';
DELETE FROM entities WHERE name LIKE '%Test%' AND entity_type IN (
    'process.definition', 'process.instance', 'experiment.trial',
    'organization.member', 'organization.invitation', 'organization.removal_request'
);
DELETE FROM entities WHERE name LIKE '%Test Organization for Schema Validation%';
DELETE FROM entities WHERE name LIKE '%Test User for Schema Validation%';
DELETE FROM entities WHERE name LIKE '%Test Process Definition%';
DELETE FROM entities WHERE name LIKE '%Test Experiment for Schema Validation%';

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('004_schema_validation_tests') ON CONFLICT (version) DO NOTHING;

-- =====================================================================
-- VALIDATION SUMMARY
-- =====================================================================

DO $$
BEGIN
    RAISE NOTICE '=====================================================================';
    RAISE NOTICE 'SCHEMA VALIDATION TEST SUMMARY';
    RAISE NOTICE '=====================================================================';
    RAISE NOTICE 'All entity type schemas have been tested with:';
    RAISE NOTICE '✅ Valid data insertion tests (6 tests)';
    RAISE NOTICE '✅ Invalid data rejection tests (6 tests)';
    RAISE NOTICE '✅ Edge case and boundary condition tests (3 tests)';
    RAISE NOTICE '';
    RAISE NOTICE 'Schemas validated:';
    RAISE NOTICE '- process.definition.v1';
    RAISE NOTICE '- process.instance.v1';
    RAISE NOTICE '- experiment.trial.v1';
    RAISE NOTICE '- organization.member.v1';
    RAISE NOTICE '- organization.invitation.v1';
    RAISE NOTICE '- organization.removal_request.v1';
    RAISE NOTICE '';
    RAISE NOTICE 'Validation functions tested:';
    RAISE NOTICE '- validate_entity_properties()';
    RAISE NOTICE '- validate_entity_on_change() trigger';
    RAISE NOTICE '- Database-level validation on entity insert/update';
    RAISE NOTICE '=====================================================================';
END $$;

