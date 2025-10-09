-- =====================================================================
-- Data Migration: Convert Legacy Tables to Pure Entity Architecture
-- =====================================================================
-- This migration converts data from legacy tables (processes, process_instances,
-- experiment_trials, organization_members, organization_invitations,
-- membership_removal_requests) to the entities table with proper entity types.
-- =====================================================================

-- Start transaction for atomic migration
BEGIN;

-- =====================================================================
-- BACKUP AND SAFETY MEASURES
-- =====================================================================

-- Create backup tables for rollback capability
CREATE TABLE IF NOT EXISTS backup_processes AS SELECT * FROM processes;
CREATE TABLE IF NOT EXISTS backup_process_instances AS SELECT * FROM process_instances;
CREATE TABLE IF NOT EXISTS backup_experiment_trials AS SELECT * FROM experiment_trials;
CREATE TABLE IF NOT EXISTS backup_organization_members AS SELECT * FROM organization_members;
CREATE TABLE IF NOT EXISTS backup_organization_invitations AS SELECT * FROM organization_invitations;
CREATE TABLE IF NOT EXISTS backup_membership_removal_requests AS SELECT * FROM membership_removal_requests;

-- Add comments to backup tables
COMMENT ON TABLE backup_processes IS 'Backup of processes table before entity migration';
COMMENT ON TABLE backup_process_instances IS 'Backup of process_instances table before entity migration';
COMMENT ON TABLE backup_experiment_trials IS 'Backup of experiment_trials table before entity migration';
COMMENT ON TABLE backup_organization_members IS 'Backup of organization_members table before entity migration';
COMMENT ON TABLE backup_organization_invitations IS 'Backup of organization_invitations table before entity migration';
COMMENT ON TABLE backup_membership_removal_requests IS 'Backup of membership_removal_requests table before entity migration';

-- =====================================================================
-- MIGRATION 1: PROCESSES TABLE → ENTITIES
-- =====================================================================

-- Migrate processes to entities with entity_type = 'process.definition'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    p.id,
    'process.definition'::VARCHAR(100) as entity_type,
    p.name,
    p.description,
    jsonb_build_object(
        'version', p.version,
        'process_type', p.process_type,
        'definition', p.definition,
        'is_template', p.is_template,
        'created_by', p.created_by
    ) as properties,
    p.status,
    p.organization_id,
    p.created_at,
    p.updated_at,
    TRUE as is_active
FROM processes p
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = p.id AND e.entity_type = 'process.definition'
);

-- Create events for migrated processes
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    p.id as entity_id,
    'process.definition' as entity_type,
    jsonb_build_object(
        'name', p.name,
        'version', p.version,
        'process_type', p.process_type,
        'migrated_from', 'processes'
    ) as data,
    jsonb_build_object(
        'migration_source', 'processes',
        'migration_timestamp', NOW(),
        'original_table', 'processes'
    ) as event_metadata
FROM processes p
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = p.id AND e.entity_type = 'process.definition'
);

-- =====================================================================
-- MIGRATION 2: PROCESS_INSTANCES TABLE → ENTITIES
-- =====================================================================

-- Migrate process_instances to entities with entity_type = 'process.instance'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    pi.id,
    'process.instance'::VARCHAR(100) as entity_type,
    COALESCE(pi.batch_id, 'Instance ' || pi.id::TEXT) as name,
    'Process instance for batch ' || COALESCE(pi.batch_id, 'unknown') as description,
    jsonb_build_object(
        'process_id', pi.process_id,
        'batch_id', pi.batch_id,
        'started_at', pi.started_at,
        'completed_at', pi.completed_at,
        'parameters', pi.parameters,
        'results', pi.results
    ) as properties,
    pi.status,
    NULL as organization_id, -- Will be set via relationship
    pi.started_at as created_at,
    COALESCE(pi.completed_at, pi.started_at) as updated_at,
    TRUE as is_active
FROM process_instances pi
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = pi.id AND e.entity_type = 'process.instance'
);

-- Create events for migrated process instances
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    pi.id as entity_id,
    'process.instance' as entity_type,
    jsonb_build_object(
        'process_id', pi.process_id,
        'batch_id', pi.batch_id,
        'status', pi.status,
        'migrated_from', 'process_instances'
    ) as data,
    jsonb_build_object(
        'migration_source', 'process_instances',
        'migration_timestamp', NOW(),
        'original_table', 'process_instances'
    ) as event_metadata
FROM process_instances pi
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = pi.id AND e.entity_type = 'process.instance'
);

-- =====================================================================
-- MIGRATION 3: EXPERIMENT_TRIALS TABLE → ENTITIES
-- =====================================================================

-- Migrate experiment_trials to entities with entity_type = 'experiment.trial'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    et.id,
    'experiment.trial'::VARCHAR(100) as entity_type,
    'Trial ' || et.trial_number::TEXT as name,
    'Experiment trial #' || et.trial_number::TEXT as description,
    jsonb_build_object(
        'experiment_id', et.experiment_id,
        'trial_number', et.trial_number,
        'started_at', et.started_at,
        'completed_at', et.completed_at,
        'parameters', et.parameters,
        'results', et.results,
        'error_message', et.error_message,
        'created_by', et.created_by
    ) as properties,
    et.status,
    NULL as organization_id, -- Will be set via relationship
    et.created_at,
    et.updated_at,
    TRUE as is_active
FROM experiment_trials et
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = et.id AND e.entity_type = 'experiment.trial'
);

-- Create events for migrated experiment trials
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    et.id as entity_id,
    'experiment.trial' as entity_type,
    jsonb_build_object(
        'experiment_id', et.experiment_id,
        'trial_number', et.trial_number,
        'status', et.status,
        'migrated_from', 'experiment_trials'
    ) as data,
    jsonb_build_object(
        'migration_source', 'experiment_trials',
        'migration_timestamp', NOW(),
        'original_table', 'experiment_trials'
    ) as event_metadata
FROM experiment_trials et
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = et.id AND e.entity_type = 'experiment.trial'
);

-- =====================================================================
-- MIGRATION 4: ORGANIZATION_MEMBERS TABLE → ENTITIES
-- =====================================================================

-- Migrate organization_members to entities with entity_type = 'organization.member'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    om.id,
    'organization.member'::VARCHAR(100) as entity_type,
    'Membership ' || om.id::TEXT as name,
    'Organization membership record' as description,
    jsonb_build_object(
        'organization_id', om.organization_id,
        'user_id', om.user_id,
        'role', om.role,
        'joined_at', om.joined_at,
        'invited_by', om.invited_by,
        'invited_at', om.invited_at,
        'accepted_at', om.accepted_at
    ) as properties,
    CASE WHEN om.is_active THEN 'active' ELSE 'inactive' END as status,
    om.organization_id,
    om.created_at,
    om.updated_at,
    om.is_active
FROM organization_members om
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = om.id AND e.entity_type = 'organization.member'
);

-- Create events for migrated organization members
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    om.id as entity_id,
    'organization.member' as entity_type,
    jsonb_build_object(
        'organization_id', om.organization_id,
        'user_id', om.user_id,
        'role', om.role,
        'is_active', om.is_active,
        'migrated_from', 'organization_members'
    ) as data,
    jsonb_build_object(
        'migration_source', 'organization_members',
        'migration_timestamp', NOW(),
        'original_table', 'organization_members'
    ) as event_metadata
FROM organization_members om
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = om.id AND e.entity_type = 'organization.member'
);

-- =====================================================================
-- MIGRATION 5: ORGANIZATION_INVITATIONS TABLE → ENTITIES
-- =====================================================================

-- Migrate organization_invitations to entities with entity_type = 'organization.invitation'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    oi.id,
    'organization.invitation'::VARCHAR(100) as entity_type,
    'Invitation to ' || oi.email as name,
    COALESCE(oi.message, 'Organization invitation') as description,
    jsonb_build_object(
        'organization_id', oi.organization_id,
        'email', oi.email,
        'role', oi.role,
        'invited_by', oi.invited_by,
        'invited_at', oi.invited_at,
        'expires_at', oi.expires_at,
        'accepted_at', oi.accepted_at,
        'declined_at', oi.declined_at,
        'message', oi.message
    ) as properties,
    oi.status,
    oi.organization_id,
    oi.created_at,
    oi.updated_at,
    oi.is_active
FROM organization_invitations oi
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = oi.id AND e.entity_type = 'organization.invitation'
);

-- Create events for migrated organization invitations
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    oi.id as entity_id,
    'organization.invitation' as entity_type,
    jsonb_build_object(
        'organization_id', oi.organization_id,
        'email', oi.email,
        'role', oi.role,
        'status', oi.status,
        'migrated_from', 'organization_invitations'
    ) as data,
    jsonb_build_object(
        'migration_source', 'organization_invitations',
        'migration_timestamp', NOW(),
        'original_table', 'organization_invitations'
    ) as event_metadata
FROM organization_invitations oi
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = oi.id AND e.entity_type = 'organization.invitation'
);

-- =====================================================================
-- MIGRATION 6: MEMBERSHIP_REMOVAL_REQUESTS TABLE → ENTITIES
-- =====================================================================

-- Migrate membership_removal_requests to entities with entity_type = 'organization.removal_request'
INSERT INTO entities (
    id,
    entity_type,
    name,
    description,
    properties,
    status,
    organization_id,
    created_at,
    updated_at,
    is_active
)
SELECT 
    mrr.id,
    'organization.removal_request'::VARCHAR(100) as entity_type,
    'Removal request ' || mrr.id::TEXT as name,
    COALESCE(mrr.reason, 'Membership removal request') as description,
    jsonb_build_object(
        'organization_id', mrr.organization_id,
        'user_id', mrr.user_id,
        'requested_by', mrr.requested_by,
        'requested_at', mrr.requested_at,
        'approved_by', mrr.approved_by,
        'approved_at', mrr.approved_at,
        'reason', mrr.reason,
        'admin_notes', mrr.admin_notes
    ) as properties,
    mrr.status,
    mrr.organization_id,
    mrr.created_at,
    mrr.updated_at,
    mrr.is_active
FROM membership_removal_requests mrr
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = mrr.id AND e.entity_type = 'organization.removal_request'
);

-- Create events for migrated membership removal requests
INSERT INTO events (
    event_type,
    entity_id,
    entity_type,
    data,
    event_metadata
)
SELECT 
    'entity.created' as event_type,
    mrr.id as entity_id,
    'organization.removal_request' as entity_type,
    jsonb_build_object(
        'organization_id', mrr.organization_id,
        'user_id', mrr.user_id,
        'status', mrr.status,
        'migrated_from', 'membership_removal_requests'
    ) as data,
    jsonb_build_object(
        'migration_source', 'membership_removal_requests',
        'migration_timestamp', NOW(),
        'original_table', 'membership_removal_requests'
    ) as event_metadata
FROM membership_removal_requests mrr
WHERE EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.id = mrr.id AND e.entity_type = 'organization.removal_request'
);

-- =====================================================================
-- RELATIONSHIP MAPPING
-- =====================================================================

-- Map process instances to process definitions
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    pi.id as from_entity,
    (pi.properties->>'process_id')::UUID as to_entity,
    'instance_of' as relationship_type,
    jsonb_build_object(
        'migrated_from', 'process_instances.process_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities pi
WHERE pi.entity_type = 'process.instance'
AND pi.properties->>'process_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = pi.id 
    AND r.relationship_type = 'instance_of'
);

-- Map experiment trials to experiments
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    et.id as from_entity,
    (et.properties->>'experiment_id')::UUID as to_entity,
    'trial_of' as relationship_type,
    jsonb_build_object(
        'trial_number', (et.properties->>'trial_number')::INTEGER,
        'migrated_from', 'experiment_trials.experiment_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities et
WHERE et.entity_type = 'experiment.trial'
AND et.properties->>'experiment_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = et.id 
    AND r.relationship_type = 'trial_of'
);

-- Map organization members to organizations
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    om.id as from_entity,
    (om.properties->>'organization_id')::UUID as to_entity,
    'member_of' as relationship_type,
    jsonb_build_object(
        'role', om.properties->>'role',
        'is_active', (om.properties->>'is_active')::BOOLEAN,
        'migrated_from', 'organization_members.organization_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities om
WHERE om.entity_type = 'organization.member'
AND om.properties->>'organization_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = om.id 
    AND r.relationship_type = 'member_of'
);

-- Map organization members to users
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    om.id as from_entity,
    (om.properties->>'user_id')::UUID as to_entity,
    'user_membership' as relationship_type,
    jsonb_build_object(
        'role', om.properties->>'role',
        'migrated_from', 'organization_members.user_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities om
WHERE om.entity_type = 'organization.member'
AND om.properties->>'user_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = om.id 
    AND r.relationship_type = 'user_membership'
);

-- Map organization invitations to organizations
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    oi.id as from_entity,
    (oi.properties->>'organization_id')::UUID as to_entity,
    'invitation_to' as relationship_type,
    jsonb_build_object(
        'email', oi.properties->>'email',
        'role', oi.properties->>'role',
        'status', oi.properties->>'status',
        'migrated_from', 'organization_invitations.organization_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities oi
WHERE oi.entity_type = 'organization.invitation'
AND oi.properties->>'organization_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = oi.id 
    AND r.relationship_type = 'invitation_to'
);

-- Map membership removal requests to organizations
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    mrr.id as from_entity,
    (mrr.properties->>'organization_id')::UUID as to_entity,
    'removal_request_for' as relationship_type,
    jsonb_build_object(
        'user_id', mrr.properties->>'user_id',
        'status', mrr.properties->>'status',
        'migrated_from', 'membership_removal_requests.organization_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities mrr
WHERE mrr.entity_type = 'organization.removal_request'
AND mrr.properties->>'organization_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = mrr.id 
    AND r.relationship_type = 'removal_request_for'
);

-- Map membership removal requests to users
INSERT INTO relationships (
    from_entity,
    to_entity,
    relationship_type,
    properties,
    strength,
    valid_from,
    created_by
)
SELECT DISTINCT
    mrr.id as from_entity,
    (mrr.properties->>'user_id')::UUID as to_entity,
    'removal_request_by' as relationship_type,
    jsonb_build_object(
        'requested_by', mrr.properties->>'requested_by',
        'migrated_from', 'membership_removal_requests.user_id',
        'migration_timestamp', NOW()
    ) as properties,
    1.0 as strength,
    NOW() as valid_from,
    'migration' as created_by
FROM entities mrr
WHERE mrr.entity_type = 'organization.removal_request'
AND mrr.properties->>'user_id' IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM relationships r 
    WHERE r.from_entity = mrr.id 
    AND r.relationship_type = 'removal_request_by'
);

-- =====================================================================
-- DATA VALIDATION AND VERIFICATION
-- =====================================================================

-- Create a summary of migration results
DO $$
DECLARE
    process_count INTEGER;
    process_instance_count INTEGER;
    experiment_trial_count INTEGER;
    org_member_count INTEGER;
    org_invitation_count INTEGER;
    removal_request_count INTEGER;
    relationship_count INTEGER;
BEGIN
    -- Count migrated entities
    SELECT COUNT(*) INTO process_count FROM entities WHERE entity_type = 'process.definition';
    SELECT COUNT(*) INTO process_instance_count FROM entities WHERE entity_type = 'process.instance';
    SELECT COUNT(*) INTO experiment_trial_count FROM entities WHERE entity_type = 'experiment.trial';
    SELECT COUNT(*) INTO org_member_count FROM entities WHERE entity_type = 'organization.member';
    SELECT COUNT(*) INTO org_invitation_count FROM entities WHERE entity_type = 'organization.invitation';
    SELECT COUNT(*) INTO removal_request_count FROM entities WHERE entity_type = 'organization.removal_request';
    SELECT COUNT(*) INTO relationship_count FROM relationships WHERE created_by = 'migration';
    
    -- Log migration summary
    RAISE NOTICE '=== DATA MIGRATION SUMMARY ===';
    RAISE NOTICE 'Process definitions migrated: %', process_count;
    RAISE NOTICE 'Process instances migrated: %', process_instance_count;
    RAISE NOTICE 'Experiment trials migrated: %', experiment_trial_count;
    RAISE NOTICE 'Organization members migrated: %', org_member_count;
    RAISE NOTICE 'Organization invitations migrated: %', org_invitation_count;
    RAISE NOTICE 'Removal requests migrated: %', removal_request_count;
    RAISE NOTICE 'Relationships created: %', relationship_count;
    RAISE NOTICE '================================';
END $$;

-- Record the migration
INSERT INTO schema_migrations (version) VALUES ('005_data_migration_to_entities') ON CONFLICT (version) DO NOTHING;

-- Commit the transaction
COMMIT;

-- =====================================================================
-- ROLLBACK PROCEDURE (for reference)
-- =====================================================================
-- To rollback this migration, run the following commands:
--
-- BEGIN;
-- 
-- -- Delete migrated entities
-- DELETE FROM entities WHERE entity_type IN (
--     'process.definition', 'process.instance', 'experiment.trial',
--     'organization.member', 'organization.invitation', 'organization.removal_request'
-- );
-- 
-- -- Delete migration events
-- DELETE FROM events WHERE event_metadata->>'migration_source' IS NOT NULL;
-- 
-- -- Delete migration relationships
-- DELETE FROM relationships WHERE created_by = 'migration';
-- 
-- -- Restore from backup tables
-- INSERT INTO processes SELECT * FROM backup_processes;
-- INSERT INTO process_instances SELECT * FROM backup_process_instances;
-- INSERT INTO experiment_trials SELECT * FROM backup_experiment_trials;
-- INSERT INTO organization_members SELECT * FROM backup_organization_members;
-- INSERT INTO organization_invitations SELECT * FROM backup_organization_invitations;
-- INSERT INTO membership_removal_requests SELECT * FROM backup_membership_removal_requests;
-- 
-- -- Remove migration record
-- DELETE FROM schema_migrations WHERE version = '005_data_migration_to_entities';
-- 
-- COMMIT;
-- =====================================================================
