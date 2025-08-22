-- Migration: Add experiment_trials table
-- This migration creates the experiment_trials table for tracking experiment executions

-- Create experiment_trials table
CREATE TABLE IF NOT EXISTS experiment_trials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    trial_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    parameters JSONB DEFAULT '{}', -- Trial-specific parameters
    results JSONB DEFAULT '{}', -- Trial results and data
    error_message TEXT,
    created_by UUID REFERENCES entities(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(experiment_id, trial_number)
);

-- Create indexes for the experiment_trials table
CREATE INDEX IF NOT EXISTS idx_experiment_trials_experiment_id ON experiment_trials(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_status ON experiment_trials(status);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_trial_number ON experiment_trials(trial_number);
CREATE INDEX IF NOT EXISTS idx_experiment_trials_created_by ON experiment_trials(created_by); 