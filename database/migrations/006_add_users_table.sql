-- Migration: Add user support using pure entity approach
-- Description: Creates user entities with authentication data stored in properties JSONB

-- Add organization_id column to entities table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'entities' AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE entities ADD COLUMN organization_id UUID;
    END IF;
END $$;

-- Add foreign key constraint for organization_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_entities_organization'
    ) THEN
        ALTER TABLE entities ADD CONSTRAINT fk_entities_organization 
            FOREIGN KEY (organization_id) REFERENCES entities(id);
    END IF;
END $$;

-- Create index on organization_id for faster filtering
CREATE INDEX IF NOT EXISTS idx_entities_organization_id ON entities(organization_id);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_entities_updated_at 
    BEFORE UPDATE ON entities 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a default organization for existing entities
DO $$
DECLARE
    default_org_id UUID;
BEGIN
    -- Create default organization if it doesn't exist
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
    
    -- Update existing entities to belong to default organization
    UPDATE entities 
    SET organization_id = default_org_id 
    WHERE organization_id IS NULL AND entity_type != 'organization';
END $$;

-- Create a default test user for development and testing using pure entity approach
DO $$
DECLARE
    test_user_id UUID;
    default_org_id UUID;
BEGIN
    -- Get default organization
    SELECT id INTO default_org_id FROM entities WHERE name = 'Default Organization' AND entity_type = 'organization';
    
    -- Create test user entity if it doesn't exist
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
        
        -- Log the test user creation
        RAISE NOTICE 'Test user created: test@example.com with password: testpassword123';
    END IF;
END $$; 