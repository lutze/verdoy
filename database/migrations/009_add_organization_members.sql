-- Migration: Add organization_members table
-- This migration creates the table for managing organization membership

-- Create organization_members table
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited_by UUID REFERENCES entities(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Create indexes for performance
CREATE INDEX idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX idx_org_members_role ON organization_members(role);
CREATE INDEX idx_org_members_active ON organization_members(is_active);
CREATE INDEX idx_org_members_invited_by ON organization_members(invited_by);

-- Add comment to table
COMMENT ON TABLE organization_members IS 'Organization membership records';
COMMENT ON COLUMN organization_members.role IS 'Member role: admin, member, or viewer';
COMMENT ON COLUMN organization_members.is_active IS 'Whether the membership is currently active';
COMMENT ON COLUMN organization_members.invited_by IS 'User who sent the invitation (if applicable)';
COMMENT ON COLUMN organization_members.accepted_at IS 'When the user accepted the invitation (if applicable)'; 