-- Migration: Add organization_id and created_by columns to processes table
-- This migration adds the missing columns that are defined in the Process model

-- Add organization_id column to processes table
ALTER TABLE processes ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES entities(id);

-- Add created_by column to processes table  
ALTER TABLE processes ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES entities(id);

-- Add description column to processes table
ALTER TABLE processes ADD COLUMN IF NOT EXISTS description TEXT;

-- Add is_template column to processes table
ALTER TABLE processes ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE;

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_processes_organization ON processes(organization_id);
CREATE INDEX IF NOT EXISTS idx_processes_created_by ON processes(created_by);
CREATE INDEX IF NOT EXISTS idx_processes_template ON processes(is_template);

-- Update existing processes to have default values
UPDATE processes SET 
    organization_id = NULL,
    created_by = NULL,
    description = 'Legacy process',
    is_template = FALSE
WHERE organization_id IS NULL; 