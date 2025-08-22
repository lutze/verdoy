-- Migration: Add organization_invitations table
-- This migration creates the table for managing organization invitations

-- Create organization_invitations table
CREATE TABLE organization_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    invited_by UUID NOT NULL REFERENCES entities(id),
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

-- Create indexes for performance
CREATE INDEX idx_org_invitations_org_id ON organization_invitations(organization_id);
CREATE INDEX idx_org_invitations_email ON organization_invitations(email);
CREATE INDEX idx_org_invitations_status ON organization_invitations(status);
CREATE INDEX idx_org_invitations_expires ON organization_invitations(expires_at);
CREATE INDEX idx_org_invitations_invited_by ON organization_invitations(invited_by);

-- Add comment to table
COMMENT ON TABLE organization_invitations IS 'Organization invitation records';
COMMENT ON COLUMN organization_invitations.role IS 'Role to be assigned when invitation is accepted';
COMMENT ON COLUMN organization_invitations.status IS 'Invitation status: pending, accepted, declined, or expired';
COMMENT ON COLUMN organization_invitations.expires_at IS 'When the invitation expires';
COMMENT ON COLUMN organization_invitations.message IS 'Optional message from the inviter'; 