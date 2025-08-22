-- =====================================================================
-- Database Schema Migration: Complete database structure
-- =====================================================================
-- This migration creates all tables, indexes, constraints, functions,
-- and triggers required for the LMS Evolution platform.
-- No test data is included - use 002_test_data.sql for sample data.
-- =====================================================================

-- Load required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'applied',
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    rollback_reason TEXT
);

-- =====================================================================
-- CORE TABLES
-- =====================================================================

-- Events table: Immutable record of all system changes
CREATE TABLE IF NOT EXISTS events (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    event_metadata JSONB DEFAULT '{}',
    source_node VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, id)
);

-- Convert events table to a hypertable (TimescaleDB)
DO $$
BEGIN
    -- Check if the table is already a hypertable
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables 
        WHERE table_name = 'events'
    ) THEN
        PERFORM create_hypertable('events', 'timestamp', chunk_time_interval => INTERVAL '1 day');
    END IF;
END $$;

-- Entities table: Current state of all "things" in the digital twin
-- Pure entity approach: All entities stored here with specialized fields in properties JSONB
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    organization_id UUID, -- Self-reference for organization membership
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Relationships table: Graph structure for entity connections
CREATE TABLE IF NOT EXISTS relationships (
    id BIGSERIAL PRIMARY KEY,
    from_entity UUID NOT NULL,
    to_entity UUID NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    strength DECIMAL(3,2) DEFAULT 1.0, -- Relationship strength (0.0-1.0)
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);

-- Schema catalog: Track schema definitions over time
CREATE TABLE IF NOT EXISTS schemas (
    id VARCHAR(100) PRIMARY KEY,
    version INTEGER NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,
    description TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);

-- Schema versions: Track schema versions over time
CREATE TABLE IF NOT EXISTS schema_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    definition JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schema_id, version)
);

-- Process definitions: Store recipe/process templates
CREATE TABLE IF NOT EXISTS processes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    process_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL, -- Steps, parameters, expected outcomes
    status VARCHAR(50) DEFAULT 'active',
    organization_id UUID,
    created_by UUID,
    description TEXT,
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Process instances: Track specific runs of processes
CREATE TABLE IF NOT EXISTS process_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_id UUID NOT NULL,
    batch_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    parameters JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}'
);

-- Experiment trials: Track experiment executions
CREATE TABLE IF NOT EXISTS experiment_trials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL,
    trial_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    parameters JSONB DEFAULT '{}', -- Trial-specific parameters
    results JSONB DEFAULT '{}', -- Trial results and data
    error_message TEXT,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(experiment_id, trial_number)
);

-- Organization members: Manage organization membership
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited_by UUID,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Organization invitations: Manage organization invitations
CREATE TABLE IF NOT EXISTS organization_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    invited_by UUID NOT NULL,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    declined_at TIMESTAMP WITH TIME ZONE,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(organization_id, email)
);

-- Membership removal requests: Manage membership removal requests
CREATE TABLE IF NOT EXISTS membership_removal_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    user_id UUID NOT NULL,
    requested_by UUID NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    reason TEXT,
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(organization_id, user_id)
);

-- =====================================================================
-- FOREIGN KEY CONSTRAINTS
-- =====================================================================

-- Add foreign key constraints after all tables are created
DO $$
BEGIN
    -- Entities organization_id self-reference
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_entities_organization'
    ) THEN
        ALTER TABLE entities ADD CONSTRAINT fk_entities_organization 
            FOREIGN KEY (organization_id) REFERENCES entities(id);
    END IF;

    -- Schema versions to schemas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_schema_versions_schema_id'
    ) THEN
        ALTER TABLE schema_versions ADD CONSTRAINT fk_schema_versions_schema_id
            FOREIGN KEY (schema_id) REFERENCES schemas(id);
    END IF;

    -- Relationships constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_relationships_from_entity'
    ) THEN
        ALTER TABLE relationships ADD CONSTRAINT fk_relationships_from_entity
            FOREIGN KEY (from_entity) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_relationships_to_entity'
    ) THEN
        ALTER TABLE relationships ADD CONSTRAINT fk_relationships_to_entity
            FOREIGN KEY (to_entity) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    -- Process constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_processes_organization'
    ) THEN
        ALTER TABLE processes ADD CONSTRAINT fk_processes_organization
            FOREIGN KEY (organization_id) REFERENCES entities(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_processes_created_by'
    ) THEN
        ALTER TABLE processes ADD CONSTRAINT fk_processes_created_by
            FOREIGN KEY (created_by) REFERENCES entities(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_process_instances_process'
    ) THEN
        ALTER TABLE process_instances ADD CONSTRAINT fk_process_instances_process
            FOREIGN KEY (process_id) REFERENCES processes(id);
    END IF;

    -- Experiment trials constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_experiment_trials_experiment'
    ) THEN
        ALTER TABLE experiment_trials ADD CONSTRAINT fk_experiment_trials_experiment
            FOREIGN KEY (experiment_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_experiment_trials_created_by'
    ) THEN
        ALTER TABLE experiment_trials ADD CONSTRAINT fk_experiment_trials_created_by
            FOREIGN KEY (created_by) REFERENCES entities(id);
    END IF;

    -- Organization membership constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_org_members_organization'
    ) THEN
        ALTER TABLE organization_members ADD CONSTRAINT fk_org_members_organization
            FOREIGN KEY (organization_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_org_members_user'
    ) THEN
        ALTER TABLE organization_members ADD CONSTRAINT fk_org_members_user
            FOREIGN KEY (user_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_org_members_invited_by'
    ) THEN
        ALTER TABLE organization_members ADD CONSTRAINT fk_org_members_invited_by
            FOREIGN KEY (invited_by) REFERENCES entities(id);
    END IF;

    -- Organization invitation constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_org_invitations_organization'
    ) THEN
        ALTER TABLE organization_invitations ADD CONSTRAINT fk_org_invitations_organization
            FOREIGN KEY (organization_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_org_invitations_invited_by'
    ) THEN
        ALTER TABLE organization_invitations ADD CONSTRAINT fk_org_invitations_invited_by
            FOREIGN KEY (invited_by) REFERENCES entities(id);
    END IF;

    -- Membership removal request constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_removal_requests_organization'
    ) THEN
        ALTER TABLE membership_removal_requests ADD CONSTRAINT fk_removal_requests_organization
            FOREIGN KEY (organization_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_removal_requests_user'
    ) THEN
        ALTER TABLE membership_removal_requests ADD CONSTRAINT fk_removal_requests_user
            FOREIGN KEY (user_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_removal_requests_requested_by'
    ) THEN
        ALTER TABLE membership_removal_requests ADD CONSTRAINT fk_removal_requests_requested_by
            FOREIGN KEY (requested_by) REFERENCES entities(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_removal_requests_approved_by'
    ) THEN
        ALTER TABLE membership_removal_requests ADD CONSTRAINT fk_removal_requests_approved_by
            FOREIGN KEY (approved_by) REFERENCES entities(id);
    END IF;
END $$;

-- =====================================================================
-- INDEXES
-- =====================================================================

-- Events table indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_data ON events USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_events_metadata ON events USING GIN(event_metadata);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_node);

-- Entities table indexes
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_organization ON entities(organization_id);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_active ON entities(is_active);
CREATE INDEX IF NOT EXISTS idx_entities_properties_gin ON entities USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_entities_type_org ON entities(entity_type, organization_id);
CREATE INDEX IF NOT EXISTS idx_entities_type_status ON entities(entity_type, status);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- Relationships table indexes
CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_entity);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_entity);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_time ON relationships(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_rel_properties ON relationships USING GIN(properties);
CREATE INDEX IF NOT EXISTS idx_rel_device_ownership ON relationships(from_entity, to_entity, relationship_type) 
    WHERE relationship_type = 'owns';

-- Process indexes
CREATE INDEX IF NOT EXISTS idx_processes_organization ON processes(organization_id);
CREATE INDEX IF NOT EXISTS idx_processes_created_by ON processes(created_by);
CREATE INDEX IF NOT EXISTS idx_processes_template ON processes(is_template);
CREATE INDEX IF NOT EXISTS idx_process_instances_batch ON process_instances(batch_id);
CREATE INDEX IF NOT EXISTS idx_process_instances_status ON process_instances(status);
CREATE INDEX IF NOT EXISTS idx_process_instances_started ON process_instances(started_at);

-- Experiment trials indexes
CREATE INDEX IF NOT EXISTS idx_experiment_trials_experiment_id ON experiment_trials(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_status ON experiment_trials(status);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_trial_number ON experiment_trials(trial_number);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_created_by ON experiment_trials(created_by);

-- Organization membership indexes
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(role);
CREATE INDEX IF NOT EXISTS idx_org_members_active ON organization_members(is_active);
CREATE INDEX IF NOT EXISTS idx_org_members_invited_by ON organization_members(invited_by);

-- Organization invitation indexes
CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id ON organization_invitations(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_invitations_email ON organization_invitations(email);
CREATE INDEX IF NOT EXISTS idx_org_invitations_status ON organization_invitations(status);
CREATE INDEX IF NOT EXISTS idx_org_invitations_expires ON organization_invitations(expires_at);
CREATE INDEX IF NOT EXISTS idx_org_invitations_invited_by ON organization_invitations(invited_by);

-- Membership removal request indexes
CREATE INDEX IF NOT EXISTS idx_removal_requests_org_id ON membership_removal_requests(organization_id);
CREATE INDEX IF NOT EXISTS idx_removal_requests_user_id ON membership_removal_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_removal_requests_status ON membership_removal_requests(status);
CREATE INDEX IF NOT EXISTS idx_removal_requests_requested_by ON membership_removal_requests(requested_by);
CREATE INDEX IF NOT EXISTS idx_removal_requests_approved_by ON membership_removal_requests(approved_by);

-- =====================================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to update updated_at timestamp on entities
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_entities_updated_at'
    ) THEN
        CREATE TRIGGER update_entities_updated_at 
            BEFORE UPDATE ON entities 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Function to validate JSON data against a schema
CREATE OR REPLACE FUNCTION validate_against_schema(
    data jsonb,
    schema_id varchar
) RETURNS boolean AS $$
DECLARE
    schema_def jsonb;
    field_name text;
    field_def jsonb;
BEGIN
    -- Get the schema definition
    SELECT definition INTO schema_def
    FROM schemas
    WHERE id = schema_id
    AND valid_to IS NULL;  -- Only use active schemas

    IF schema_def IS NULL THEN
        RAISE EXCEPTION 'Schema % not found or not active', schema_id;
    END IF;

    -- Check required fields
    FOR field_name, field_def IN SELECT * FROM jsonb_each(schema_def)
    LOOP
        IF (field_def->>'required')::boolean THEN
            IF data->field_name IS NULL THEN
                RAISE EXCEPTION 'Required field % is missing', field_name;
            END IF;
        END IF;

        -- Check type if specified
        IF field_def->>'type' IS NOT NULL THEN
            CASE field_def->>'type'
                WHEN 'string' THEN
                    IF jsonb_typeof(data->field_name) != 'string' THEN
                        RAISE EXCEPTION 'Field % must be a string', field_name;
                    END IF;
                WHEN 'number' THEN
                    IF jsonb_typeof(data->field_name) != 'number' THEN
                        RAISE EXCEPTION 'Field % must be a number', field_name;
                    END IF;
                WHEN 'datetime' THEN
                    -- For datetime, we'll just check if it's a string
                    -- that can be parsed as a timestamp
                    IF jsonb_typeof(data->field_name) != 'string' THEN
                        RAISE EXCEPTION 'Field % must be a datetime string', field_name;
                    END IF;
                    BEGIN
                        PERFORM (data->>field_name)::timestamp;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'Field % must be a valid datetime', field_name;
                    END;
                WHEN 'array' THEN
                    IF jsonb_typeof(data->field_name) != 'array' THEN
                        RAISE EXCEPTION 'Field % must be an array', field_name;
                    END IF;
            END CASE;
        END IF;

        -- Check enum values if specified
        IF field_def->'enum' IS NOT NULL THEN
            IF NOT (data->>field_name) = ANY(ARRAY(SELECT jsonb_array_elements_text(field_def->'enum'))) THEN
                RAISE EXCEPTION 'Field % must be one of: %', 
                    field_name, 
                    array_to_string(ARRAY(SELECT jsonb_array_elements_text(field_def->'enum')), ', ');
            END IF;
        END IF;

        -- Check min/max for numbers
        IF field_def->>'type' = 'number' THEN
            IF field_def->>'min' IS NOT NULL AND (data->>field_name)::numeric < (field_def->>'min')::numeric THEN
                RAISE EXCEPTION 'Field % must be greater than or equal to %', field_name, field_def->>'min';
            END IF;
            IF field_def->>'max' IS NOT NULL AND (data->>field_name)::numeric > (field_def->>'max')::numeric THEN
                RAISE EXCEPTION 'Field % must be less than or equal to %', field_name, field_def->>'max';
            END IF;
        END IF;
    END LOOP;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- TIMESCALEDB CONFIGURATION
-- =====================================================================

-- Set up data retention policy (optional)
DO $$
BEGIN
    -- Check if retention policy already exists
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.jobs 
        WHERE job_type = 'drop_chunks' 
        AND config->>'hypertable_name' = 'events'
    ) THEN
        PERFORM add_retention_policy('events', INTERVAL '2 years');
    END IF;
END $$;

-- =====================================================================
-- TABLE COMMENTS
-- =====================================================================

-- Add comments to tables for documentation
COMMENT ON TABLE organization_members IS 'Organization membership records';
COMMENT ON COLUMN organization_members.role IS 'Member role: admin, member, or viewer';
COMMENT ON COLUMN organization_members.is_active IS 'Whether the membership is currently active';
COMMENT ON COLUMN organization_members.invited_by IS 'User who sent the invitation (if applicable)';
COMMENT ON COLUMN organization_members.accepted_at IS 'When the user accepted the invitation (if applicable)';

COMMENT ON TABLE organization_invitations IS 'Organization invitation records';
COMMENT ON COLUMN organization_invitations.role IS 'Role to be assigned when invitation is accepted';
COMMENT ON COLUMN organization_invitations.status IS 'Invitation status: pending, accepted, declined, or expired';
COMMENT ON COLUMN organization_invitations.expires_at IS 'When the invitation expires';
COMMENT ON COLUMN organization_invitations.message IS 'Optional message from the inviter';

COMMENT ON TABLE membership_removal_requests IS 'Membership removal request records';
COMMENT ON COLUMN membership_removal_requests.status IS 'Request status: pending, approved, or denied';
COMMENT ON COLUMN membership_removal_requests.reason IS 'User-provided reason for removal request';
COMMENT ON COLUMN membership_removal_requests.admin_notes IS 'Admin notes on approval/denial decision';

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('001_schema') ON CONFLICT (version) DO NOTHING;
