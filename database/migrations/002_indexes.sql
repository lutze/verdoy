-- Events table indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_data ON events USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_events_metadata ON events USING GIN(event_metadata);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_node);

-- Entities table indexes
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_properties ON entities USING GIN(properties);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- Relationships table indexes
CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_entity);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_entity);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_time ON relationships(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_rel_properties ON relationships USING GIN(properties);

-- Device ownership indexes
CREATE INDEX IF NOT EXISTS idx_rel_device_ownership ON relationships(from_entity, to_entity, relationship_type) 
    WHERE relationship_type = 'owns';

-- Process indexes
CREATE INDEX IF NOT EXISTS idx_process_instances_batch ON process_instances(batch_id);
CREATE INDEX IF NOT EXISTS idx_process_instances_status ON process_instances(status);
CREATE INDEX IF NOT EXISTS idx_process_instances_started ON process_instances(started_at); 