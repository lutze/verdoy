-- Events table: Immutable record of all system changes
CREATE TABLE IF NOT EXISTS events (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    event_metadata JSONB DEFAULT '{}',
    source_node VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, id)
);

-- Convert events table to a hypertable
SELECT create_hypertable('events', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Entities table: Current state of all "things" in the digital twin
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Relationships table: Graph structure for entity connections
CREATE TABLE IF NOT EXISTS relationships (
    id BIGSERIAL PRIMARY KEY,
    from_entity UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    to_entity UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    strength DECIMAL(3,2) DEFAULT 1.0, -- Relationship strength (0.0-1.0)
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);

-- Schema catalog: Track schema definitions over time
CREATE TABLE IF NOT EXISTS schemas (
    id VARCHAR(100) PRIMARY KEY,
    version INTEGER NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,
    description TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);

-- Schema versions: Track schema versions over time
CREATE TABLE IF NOT EXISTS schema_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id VARCHAR(255) NOT NULL REFERENCES schemas(id),
    version INTEGER NOT NULL,
    definition JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schema_id, version)
);

-- Process definitions: Store recipe/process templates
CREATE TABLE IF NOT EXISTS processes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    process_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL, -- Steps, parameters, expected outcomes
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Process instances: Track specific runs of processes
CREATE TABLE IF NOT EXISTS process_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_id UUID NOT NULL REFERENCES processes(id),
    batch_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    parameters JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}'
);