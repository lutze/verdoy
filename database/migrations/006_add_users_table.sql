-- Migration: Add users table and organization support
-- Description: Creates users table for authentication and adds organization_id to entities

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

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create index on entity_id for faster joins
CREATE INDEX IF NOT EXISTS idx_users_entity_id ON users(entity_id);

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

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
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

-- Create a default test user for development and testing
DO $$
DECLARE
    user_entity_id UUID;
    test_user_id UUID;
BEGIN
    -- Create user entity if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM entities WHERE entity_type = 'user' AND name = 'Test User') THEN
        INSERT INTO entities (id, entity_type, name, description, properties, is_active) VALUES
        (
            uuid_generate_v4(),
            'user',
            'Test User',
            'Default test user for development and testing',
            '{
                "email": "test@example.com",
                "user_type": "standard",
                "role": "admin",
                "department": "Development",
                "created_by": "system"
            }',
            true
        ) RETURNING id INTO user_entity_id;
    ELSE
        SELECT id INTO user_entity_id FROM entities WHERE entity_type = 'user' AND name = 'Test User';
    END IF;

    -- Create user record if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'test@example.com') THEN
        INSERT INTO users (id, entity_id, email, hashed_password, is_active, is_superuser, created_at, updated_at) VALUES
        (
            uuid_generate_v4(),
            user_entity_id,
            'test@example.com',
            '$2b$12$2KKaRCpDxQcm2p99qfGoCerZaHWaNd3/cKiT7QvsyNQ.jslRWV5da', -- password: "testpassword123"
            true,
            false,
            NOW(),
            NOW()
        );
    END IF;
    
    -- Log the test user creation
    RAISE NOTICE 'Test user created: test@example.com with password: testpassword123';
END $$; 