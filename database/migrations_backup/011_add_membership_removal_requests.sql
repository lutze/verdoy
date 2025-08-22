-- Migration: Add membership_removal_requests table
-- This migration creates the table for managing membership removal requests

-- Create membership_removal_requests table
CREATE TABLE membership_removal_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES entities(id),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
    approved_by UUID REFERENCES entities(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    reason TEXT,
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(organization_id, user_id)
);

-- Create indexes for performance
CREATE INDEX idx_removal_requests_org_id ON membership_removal_requests(organization_id);
CREATE INDEX idx_removal_requests_user_id ON membership_removal_requests(user_id);
CREATE INDEX idx_removal_requests_status ON membership_removal_requests(status);
CREATE INDEX idx_removal_requests_requested_by ON membership_removal_requests(requested_by);
CREATE INDEX idx_removal_requests_approved_by ON membership_removal_requests(approved_by);

-- Add comment to table
COMMENT ON TABLE membership_removal_requests IS 'Membership removal request records';
COMMENT ON COLUMN membership_removal_requests.status IS 'Request status: pending, approved, or denied';
COMMENT ON COLUMN membership_removal_requests.reason IS 'User-provided reason for removal request';
COMMENT ON COLUMN membership_removal_requests.admin_notes IS 'Admin notes on approval/denial decision'; 