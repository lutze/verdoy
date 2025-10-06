-- =====================================================================
-- Database Schema Migration: Entity Type Schemas
-- =====================================================================
-- This migration creates JSON schemas for entity types that will replace
-- the separate tables: processes, process_instances, experiment_trials,
-- organization_members, organization_invitations, membership_removal_requests
-- 
-- This follows the single-table inheritance pattern where all entities
-- are stored in the entities table with entity_type differentiation
-- and specialized properties in the JSONB properties column.
-- =====================================================================

-- =====================================================================
-- PROCESS DEFINITION SCHEMA (LUT-93)
-- =====================================================================

-- Schema for process.definition entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'process.definition.v1',
    1,
    'process.definition',
    '{
        "name": {
            "type": "string",
            "required": true,
            "minLength": 1,
            "maxLength": 200,
            "description": "Human-readable name of the process definition"
        },
        "version": {
            "type": "string",
            "required": true,
            "pattern": "^[0-9]+\\.[0-9]+(\\.[0-9]+)?$",
            "description": "Semantic version of the process definition (e.g., 1.0, 1.2.3)"
        },
        "process_type": {
            "type": "string",
            "required": true,
            "enum": ["baking", "fermentation", "extraction", "purification", "analysis", "custom"],
            "description": "Type/category of the process"
        },
        "definition": {
            "type": "object",
            "required": true,
            "properties": {
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "required": true},
                            "duration": {"type": "number", "minimum": 0},
                            "targetTemp": {"type": "number"},
                            "targetPh": {"type": "number", "minimum": 0, "maximum": 14},
                            "targetDo": {"type": "number", "minimum": 0, "maximum": 100},
                            "description": {"type": "string"}
                        }
                    }
                },
                "expectedResults": {
                    "type": "object",
                    "additionalProperties": true
                },
                "safetyParameters": {
                    "type": "object",
                    "additionalProperties": true
                }
            },
            "description": "Process definition containing stages, parameters, and expected outcomes"
        },
        "status": {
            "type": "string",
            "required": true,
            "enum": ["draft", "active", "deprecated", "archived"],
            "default": "draft",
            "description": "Current status of the process definition"
        },
        "description": {
            "type": "string",
            "required": true,
            "maxLength": 1000,
            "description": "Detailed description of the process"
        },
        "is_template": {
            "type": "boolean",
            "required": true,
            "default": false,
            "description": "Whether this is a template that can be used to create instances"
        },
        "organization_id": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the organization that owns this process definition"
        },
        "created_by": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the user who created this process definition"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags for categorizing and searching process definitions"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the process definition"
        }
    }',
    'Process definition schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- PROCESS INSTANCE SCHEMA (LUT-94)
-- =====================================================================

-- Schema for process.instance entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'process.instance.v1',
    1,
    'process.instance',
    '{
        "process_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the process definition this instance is based on"
        },
        "batch_id": {
            "type": "string",
            "maxLength": 100,
            "description": "Batch identifier for this process instance"
        },
        "status": {
            "type": "string",
            "required": true,
            "enum": ["pending", "running", "paused", "completed", "failed", "cancelled"],
            "default": "pending",
            "description": "Current status of the process instance"
        },
        "started_at": {
            "type": "string",
            "required": true,
            "format": "date-time",
            "description": "When the process instance was started"
        },
        "completed_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the process instance was completed (if applicable)"
        },
        "parameters": {
            "type": "object",
            "default": {},
            "description": "Instance-specific parameters that override or supplement the process definition"
        },
        "results": {
            "type": "object",
            "default": {},
            "description": "Results and data collected during process execution"
        },
        "current_stage": {
            "type": "string",
            "description": "Name of the current stage being executed"
        },
        "progress_percentage": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 0,
            "description": "Overall progress percentage of the process instance"
        },
        "error_message": {
            "type": "string",
            "description": "Error message if the process instance failed"
        },
        "operator": {
            "type": "string",
            "description": "Name or ID of the operator running this process instance"
        },
        "equipment_id": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the equipment/device running this process instance"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the process instance"
        }
    }',
    'Process instance schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- EXPERIMENT TRIAL SCHEMA (LUT-95)
-- =====================================================================

-- Schema for experiment.trial entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'experiment.trial.v1',
    1,
    'experiment.trial',
    '{
        "experiment_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the experiment this trial belongs to"
        },
        "trial_number": {
            "type": "integer",
            "required": true,
            "minimum": 1,
            "description": "Sequential trial number within the experiment"
        },
        "status": {
            "type": "string",
            "required": true,
            "enum": ["pending", "running", "completed", "failed", "cancelled"],
            "default": "pending",
            "description": "Current status of the trial"
        },
        "started_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the trial was started"
        },
        "completed_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the trial was completed (if applicable)"
        },
        "parameters": {
            "type": "object",
            "default": {},
            "description": "Trial-specific parameters and settings"
        },
        "results": {
            "type": "object",
            "default": {},
            "description": "Results and data collected during the trial"
        },
        "error_message": {
            "type": "string",
            "description": "Error message if the trial failed"
        },
        "created_by": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the user who created this trial"
        },
        "notes": {
            "type": "string",
            "description": "Additional notes or observations about the trial"
        },
        "quality_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Quality score for the trial results (0-100)"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the trial"
        }
    }',
    'Experiment trial schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- ORGANIZATION MEMBER SCHEMA (LUT-96)
-- =====================================================================

-- Schema for organization.member entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'organization.member.v1',
    1,
    'organization.member',
    '{
        "organization_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the organization"
        },
        "user_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the user"
        },
        "role": {
            "type": "string",
            "required": true,
            "enum": ["admin", "member", "viewer"],
            "default": "member",
            "description": "Role of the user in the organization"
        },
        "is_active": {
            "type": "boolean",
            "required": true,
            "default": true,
            "description": "Whether the membership is currently active"
        },
        "invited_by": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the user who sent the invitation"
        },
        "invited_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the invitation was sent"
        },
        "accepted_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the user accepted the invitation"
        },
        "joined_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the user officially joined the organization"
        },
        "permissions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific permissions granted to this member"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the membership"
        }
    }',
    'Organization member schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- ORGANIZATION INVITATION SCHEMA (LUT-97)
-- =====================================================================

-- Schema for organization.invitation entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'organization.invitation.v1',
    1,
    'organization.invitation',
    '{
        "organization_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the organization"
        },
        "email": {
            "type": "string",
            "required": true,
            "format": "email",
            "maxLength": 255,
            "description": "Email address of the person being invited"
        },
        "role": {
            "type": "string",
            "required": true,
            "enum": ["admin", "member", "viewer"],
            "default": "member",
            "description": "Role to be assigned when invitation is accepted"
        },
        "status": {
            "type": "string",
            "required": true,
            "enum": ["pending", "accepted", "declined", "expired"],
            "default": "pending",
            "description": "Current status of the invitation"
        },
        "invited_by": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the user who sent the invitation"
        },
        "expires_at": {
            "type": "string",
            "required": true,
            "format": "date-time",
            "description": "When the invitation expires"
        },
        "accepted_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the invitation was accepted"
        },
        "declined_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the invitation was declined"
        },
        "message": {
            "type": "string",
            "maxLength": 1000,
            "description": "Optional message from the inviter"
        },
        "invitation_token": {
            "type": "string",
            "description": "Unique token for the invitation link"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the invitation"
        }
    }',
    'Organization invitation schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- MEMBERSHIP REMOVAL REQUEST SCHEMA (LUT-98)
-- =====================================================================

-- Schema for organization.removal_request entity type
INSERT INTO schemas (id, version, entity_type, definition, description, valid_from, valid_to, created_by) VALUES
(
    'organization.removal_request.v1',
    1,
    'organization.removal_request',
    '{
        "organization_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the organization"
        },
        "user_id": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the user to be removed"
        },
        "requested_by": {
            "type": "string",
            "required": true,
            "format": "uuid",
            "description": "UUID of the user who requested the removal"
        },
        "status": {
            "type": "string",
            "required": true,
            "enum": ["pending", "approved", "denied"],
            "default": "pending",
            "description": "Current status of the removal request"
        },
        "approved_by": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of the admin who approved/denied the request"
        },
        "approved_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the request was approved or denied"
        },
        "reason": {
            "type": "string",
            "maxLength": 1000,
            "description": "User-provided reason for the removal request"
        },
        "admin_notes": {
            "type": "string",
            "maxLength": 1000,
            "description": "Admin notes on the approval/denial decision"
        },
        "requested_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the removal request was submitted"
        },
        "metadata": {
            "type": "object",
            "additionalProperties": true,
            "description": "Additional metadata for the removal request"
        }
    }',
    'Membership removal request schema for single-table inheritance',
    NOW(),
    NULL,
    'system'
) ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- VALIDATION FUNCTIONS
-- =====================================================================

-- Function to validate entity properties against their schema
CREATE OR REPLACE FUNCTION validate_entity_properties(
    entity_type_param VARCHAR(100),
    properties_param JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    schema_def JSONB;
    field_name TEXT;
    field_def JSONB;
    field_value JSONB;
    enum_values TEXT[];
BEGIN
    -- Get the latest schema for the entity type
    SELECT definition INTO schema_def
    FROM schemas
    WHERE schemas.entity_type = entity_type_param
    AND valid_to IS NULL
    ORDER BY version DESC
    LIMIT 1;

    IF schema_def IS NULL THEN
        RAISE EXCEPTION 'No active schema found for entity type: %', entity_type_param;
    END IF;

    -- Validate each field in the schema
    FOR field_name, field_def IN SELECT * FROM jsonb_each(schema_def)
    LOOP
        field_value := properties_param->field_name;
        
        -- Check required fields
        IF (field_def->>'required')::boolean AND field_value IS NULL THEN
            RAISE EXCEPTION 'Required field "%" is missing for entity type %', field_name, entity_type_param;
        END IF;

        -- Skip validation if field is null and not required
        IF field_value IS NULL THEN
            CONTINUE;
        END IF;

        -- Check type if specified
        IF field_def->>'type' IS NOT NULL THEN
            CASE field_def->>'type'
                WHEN 'string' THEN
                    IF jsonb_typeof(field_value) != 'string' THEN
                        RAISE EXCEPTION 'Field "%" must be a string for entity type %', field_name, entity_type_param;
                    END IF;
                    
                    -- Check string length constraints
                    IF field_def->>'minLength' IS NOT NULL AND length(field_value #>> '{}') < (field_def->>'minLength')::integer THEN
                        RAISE EXCEPTION 'Field "%" must be at least % characters for entity type %', field_name, field_def->>'minLength', entity_type_param;
                    END IF;
                    
                    IF field_def->>'maxLength' IS NOT NULL AND length(field_value #>> '{}') > (field_def->>'maxLength')::integer THEN
                        RAISE EXCEPTION 'Field "%" must be at most % characters for entity type %', field_name, field_def->>'maxLength', entity_type_param;
                    END IF;
                    
                WHEN 'integer' THEN
                    IF jsonb_typeof(field_value) != 'number' OR (field_value #>> '{}')::numeric % 1 != 0 THEN
                        RAISE EXCEPTION 'Field "%" must be an integer for entity type %', field_name, entity_type_param;
                    END IF;
                    
                WHEN 'number' THEN
                    IF jsonb_typeof(field_value) != 'number' THEN
                        RAISE EXCEPTION 'Field "%" must be a number for entity type %', field_name, entity_type_param;
                    END IF;
                    
                WHEN 'boolean' THEN
                    IF jsonb_typeof(field_value) != 'boolean' THEN
                        RAISE EXCEPTION 'Field "%" must be a boolean for entity type %', field_name, entity_type_param;
                    END IF;
                    
                WHEN 'array' THEN
                    IF jsonb_typeof(field_value) != 'array' THEN
                        RAISE EXCEPTION 'Field "%" must be an array for entity type %', field_name, entity_type_param;
                    END IF;
                    
                WHEN 'object' THEN
                    IF jsonb_typeof(field_value) != 'object' THEN
                        RAISE EXCEPTION 'Field "%" must be an object for entity type %', field_name, entity_type_param;
                    END IF;
            END CASE;
        END IF;

        -- Check enum values if specified
        IF field_def->'enum' IS NOT NULL THEN
            enum_values := ARRAY(SELECT jsonb_array_elements_text(field_def->'enum'));
            IF NOT (field_value #>> '{}') = ANY(enum_values) THEN
                RAISE EXCEPTION 'Field "%" must be one of: % for entity type %', 
                    field_name, 
                    array_to_string(enum_values, ', '),
                    entity_type_param;
            END IF;
        END IF;

        -- Check numeric constraints
        IF field_def->>'type' IN ('number', 'integer') THEN
            IF field_def->>'minimum' IS NOT NULL AND (field_value #>> '{}')::numeric < (field_def->>'minimum')::numeric THEN
                RAISE EXCEPTION 'Field "%" must be greater than or equal to % for entity type %', field_name, field_def->>'minimum', entity_type_param;
            END IF;
            IF field_def->>'maximum' IS NOT NULL AND (field_value #>> '{}')::numeric > (field_def->>'maximum')::numeric THEN
                RAISE EXCEPTION 'Field "%" must be less than or equal to % for entity type %', field_name, field_def->>'maximum', entity_type_param;
            END IF;
        END IF;

        -- Check format constraints
        IF field_def->>'format' IS NOT NULL THEN
            CASE field_def->>'format'
                WHEN 'uuid' THEN
                    -- Basic UUID format check
                    IF NOT (field_value #>> '{}') ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
                        RAISE EXCEPTION 'Field "%" must be a valid UUID for entity type %', field_name, entity_type_param;
                    END IF;
                WHEN 'email' THEN
                    -- Basic email format check
                    IF NOT (field_value #>> '{}') ~ '^[^@]+@[^@]+\.[^@]+$' THEN
                        RAISE EXCEPTION 'Field "%" must be a valid email address for entity type %', field_name, entity_type_param;
                    END IF;
                WHEN 'date-time' THEN
                    -- Basic datetime format check
                    BEGIN
                        PERFORM (field_value #>> '{}')::timestamp;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'Field "%" must be a valid datetime for entity type %', field_name, entity_type_param;
                    END;
            END CASE;
        END IF;

        -- Check pattern constraints
        IF field_def->>'pattern' IS NOT NULL THEN
            IF NOT (field_value #>> '{}') ~ (field_def->>'pattern') THEN
                RAISE EXCEPTION 'Field "%" must match pattern "%" for entity type %', field_name, field_def->>'pattern', entity_type_param;
            END IF;
        END IF;
    END LOOP;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- TRIGGER FUNCTION FOR ENTITY VALIDATION
-- =====================================================================

-- Function to validate entity properties on insert/update
CREATE OR REPLACE FUNCTION validate_entity_on_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate properties against schema if entity_type is one of our new types
    IF NEW.entity_type IN (
        'process.definition', 'process.instance', 'experiment.trial',
        'organization.member', 'organization.invitation', 'organization.removal_request'
    ) THEN
        PERFORM validate_entity_properties(NEW.entity_type, NEW.properties);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for entity validation
DROP TRIGGER IF EXISTS validate_entity_trigger ON entities;
CREATE TRIGGER validate_entity_trigger
    BEFORE INSERT OR UPDATE ON entities
    FOR EACH ROW
    EXECUTE FUNCTION validate_entity_on_change();

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('003_entity_schemas') ON CONFLICT (version) DO NOTHING;

