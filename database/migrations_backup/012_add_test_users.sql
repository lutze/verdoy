-- Migration: Add test users and organization memberships
-- This migration creates test users and adds them to organizations as members

DO $$
DECLARE
    org1_id UUID;
    org2_id UUID;
    user1_id UUID;
    user2_id UUID;
    user3_id UUID;
BEGIN
    -- Get organization IDs
    SELECT id INTO org1_id FROM entities WHERE name = 'Acme Research Labs' AND entity_type = 'organization';
    SELECT id INTO org2_id FROM entities WHERE name = 'BioTech Innovations' AND entity_type = 'organization';
    
    -- Insert test users if they don't exist
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