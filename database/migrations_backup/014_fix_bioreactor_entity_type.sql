-- Migration: Fix bioreactor entity_type to match service expectations
-- This migration updates the Acme Bioreactor BR-001 entity_type from 'bioreactor' to 'device.bioreactor'

-- Update the bioreactor entity_type to match service expectations
UPDATE entities 
SET entity_type = 'device.bioreactor'
WHERE name = 'Acme Bioreactor BR-001' 
AND entity_type = 'bioreactor';
