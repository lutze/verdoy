--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: validate_against_schema(jsonb, character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.validate_against_schema(data jsonb, schema_id character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    schema_def jsonb;
    field_name text;
    field_def jsonb;
BEGIN
    -- Get the schema definition
    SELECT definition INTO schema_def
    FROM schemas
    WHERE id = schema_id
    AND valid_to IS NULL;  -- Only use active schemas

    IF schema_def IS NULL THEN
        RAISE EXCEPTION 'Schema % not found or not active', schema_id;
    END IF;

    -- Check required fields
    FOR field_name, field_def IN SELECT * FROM jsonb_each(schema_def)
    LOOP
        IF (field_def->>'required')::boolean THEN
            IF data->field_name IS NULL THEN
                RAISE EXCEPTION 'Required field % is missing', field_name;
            END IF;
        END IF;

        -- Check type if specified
        IF field_def->>'type' IS NOT NULL THEN
            CASE field_def->>'type'
                WHEN 'string' THEN
                    IF jsonb_typeof(data->field_name) != 'string' THEN
                        RAISE EXCEPTION 'Field % must be a string', field_name;
                    END IF;
                WHEN 'number' THEN
                    IF jsonb_typeof(data->field_name) != 'number' THEN
                        RAISE EXCEPTION 'Field % must be a number', field_name;
                    END IF;
                WHEN 'datetime' THEN
                    -- For datetime, we'll just check if it's a string
                    -- that can be parsed as a timestamp
                    IF jsonb_typeof(data->field_name) != 'string' THEN
                        RAISE EXCEPTION 'Field % must be a datetime string', field_name;
                    END IF;
                    BEGIN
                        PERFORM (data->>field_name)::timestamp;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE EXCEPTION 'Field % must be a valid datetime', field_name;
                    END;
                WHEN 'array' THEN
                    IF jsonb_typeof(data->field_name) != 'array' THEN
                        RAISE EXCEPTION 'Field % must be an array', field_name;
                    END IF;
            END CASE;
        END IF;

        -- Check enum values if specified
        IF field_def->'enum' IS NOT NULL THEN
            IF NOT (data->>field_name) = ANY(ARRAY(SELECT jsonb_array_elements_text(field_def->'enum'))) THEN
                RAISE EXCEPTION 'Field % must be one of: %', 
                    field_name, 
                    array_to_string(ARRAY(SELECT jsonb_array_elements_text(field_def->'enum')), ', ');
            END IF;
        END IF;

        -- Check min/max for numbers
        IF field_def->>'type' = 'number' THEN
            IF field_def->>'min' IS NOT NULL AND (data->>field_name)::numeric < (field_def->>'min')::numeric THEN
                RAISE EXCEPTION 'Field % must be greater than or equal to %', field_name, field_def->>'min';
            END IF;
            IF field_def->>'max' IS NOT NULL AND (data->>field_name)::numeric > (field_def->>'max')::numeric THEN
                RAISE EXCEPTION 'Field % must be less than or equal to %', field_name, field_def->>'max';
            END IF;
        END IF;
    END LOOP;

    RETURN true;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.events (
    id bigint NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    event_type character varying(100) NOT NULL,
    entity_id uuid NOT NULL,
    entity_type character varying(100) NOT NULL,
    data jsonb NOT NULL,
    event_metadata jsonb DEFAULT '{}'::jsonb,
    source_node character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: _hyper_1_1_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_1_1_chunk (
    CONSTRAINT constraint_1 CHECK ((("timestamp" >= '2025-08-30 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-08-31 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.events);


--
-- Name: entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entities (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    entity_type character varying(100) NOT NULL,
    name text NOT NULL,
    description text,
    properties jsonb DEFAULT '{}'::jsonb NOT NULL,
    status character varying(50) DEFAULT 'active'::character varying,
    organization_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.events ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: experiment_trials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.experiment_trials (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    experiment_id uuid NOT NULL,
    trial_number integer NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    parameters jsonb DEFAULT '{}'::jsonb,
    results jsonb DEFAULT '{}'::jsonb,
    error_message text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: membership_removal_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.membership_removal_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    requested_by uuid NOT NULL,
    requested_at timestamp with time zone DEFAULT now(),
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    approved_by uuid,
    approved_at timestamp with time zone,
    reason text,
    admin_notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    CONSTRAINT membership_removal_requests_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'denied'::character varying])::text[])))
);


--
-- Name: TABLE membership_removal_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.membership_removal_requests IS 'Membership removal request records';


--
-- Name: COLUMN membership_removal_requests.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.membership_removal_requests.status IS 'Request status: pending, approved, or denied';


--
-- Name: COLUMN membership_removal_requests.reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.membership_removal_requests.reason IS 'User-provided reason for removal request';


--
-- Name: COLUMN membership_removal_requests.admin_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.membership_removal_requests.admin_notes IS 'Admin notes on approval/denial decision';


--
-- Name: organization_invitations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organization_invitations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    role character varying(50) DEFAULT 'member'::character varying NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    invited_by uuid NOT NULL,
    invited_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone NOT NULL,
    accepted_at timestamp with time zone,
    declined_at timestamp with time zone,
    message text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    CONSTRAINT organization_invitations_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'member'::character varying, 'viewer'::character varying])::text[]))),
    CONSTRAINT organization_invitations_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'accepted'::character varying, 'declined'::character varying, 'expired'::character varying])::text[])))
);


--
-- Name: TABLE organization_invitations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.organization_invitations IS 'Organization invitation records';


--
-- Name: COLUMN organization_invitations.role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_invitations.role IS 'Role to be assigned when invitation is accepted';


--
-- Name: COLUMN organization_invitations.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_invitations.status IS 'Invitation status: pending, accepted, declined, or expired';


--
-- Name: COLUMN organization_invitations.expires_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_invitations.expires_at IS 'When the invitation expires';


--
-- Name: COLUMN organization_invitations.message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_invitations.message IS 'Optional message from the inviter';


--
-- Name: organization_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organization_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member'::character varying NOT NULL,
    is_active boolean DEFAULT true,
    joined_at timestamp with time zone DEFAULT now(),
    invited_by uuid,
    invited_at timestamp with time zone DEFAULT now(),
    accepted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT organization_members_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'member'::character varying, 'viewer'::character varying])::text[])))
);


--
-- Name: TABLE organization_members; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.organization_members IS 'Organization membership records';


--
-- Name: COLUMN organization_members.role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_members.role IS 'Member role: admin, member, or viewer';


--
-- Name: COLUMN organization_members.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_members.is_active IS 'Whether the membership is currently active';


--
-- Name: COLUMN organization_members.invited_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_members.invited_by IS 'User who sent the invitation (if applicable)';


--
-- Name: COLUMN organization_members.accepted_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.organization_members.accepted_at IS 'When the user accepted the invitation (if applicable)';


--
-- Name: process_instances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.process_instances (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    process_id uuid NOT NULL,
    batch_id character varying(100),
    status character varying(50) DEFAULT 'running'::character varying,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    parameters jsonb DEFAULT '{}'::jsonb,
    results jsonb DEFAULT '{}'::jsonb
);


--
-- Name: processes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.processes (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(200) NOT NULL,
    version character varying(20) NOT NULL,
    process_type character varying(100) NOT NULL,
    definition jsonb NOT NULL,
    status character varying(50) DEFAULT 'active'::character varying,
    organization_id uuid,
    created_by uuid,
    description text,
    is_template boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationships (
    id bigint NOT NULL,
    from_entity uuid NOT NULL,
    to_entity uuid NOT NULL,
    relationship_type character varying(100) NOT NULL,
    properties jsonb DEFAULT '{}'::jsonb,
    strength numeric(3,2) DEFAULT 1.0,
    valid_from timestamp with time zone DEFAULT now() NOT NULL,
    valid_to timestamp with time zone,
    created_by character varying(100)
);


--
-- Name: relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.relationships_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.relationships_id_seq OWNED BY public.relationships.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL,
    applied_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(50) DEFAULT 'applied'::character varying,
    rolled_back_at timestamp with time zone,
    rollback_reason text
);


--
-- Name: schema_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    schema_id character varying(255) NOT NULL,
    version integer NOT NULL,
    definition jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: schemas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schemas (
    id character varying(100) NOT NULL,
    version integer NOT NULL,
    entity_type character varying(100) NOT NULL,
    definition jsonb NOT NULL,
    description text,
    valid_from timestamp with time zone DEFAULT now() NOT NULL,
    valid_to timestamp with time zone,
    created_by character varying(100)
);


--
-- Name: _hyper_1_1_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_1_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_1_1_chunk event_metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_1_chunk ALTER COLUMN event_metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_1_1_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_1_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships ALTER COLUMN id SET DEFAULT nextval('public.relationships_id_seq'::regclass);


--
-- Name: _hyper_1_1_chunk 1_1_events_pkey; Type: CONSTRAINT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_1_1_chunk
    ADD CONSTRAINT "1_1_events_pkey" PRIMARY KEY ("timestamp", id);


--
-- Name: entities entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_pkey PRIMARY KEY (id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY ("timestamp", id);


--
-- Name: experiment_trials experiment_trials_experiment_id_trial_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment_trials
    ADD CONSTRAINT experiment_trials_experiment_id_trial_number_key UNIQUE (experiment_id, trial_number);


--
-- Name: experiment_trials experiment_trials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment_trials
    ADD CONSTRAINT experiment_trials_pkey PRIMARY KEY (id);


--
-- Name: membership_removal_requests membership_removal_requests_organization_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT membership_removal_requests_organization_id_user_id_key UNIQUE (organization_id, user_id);


--
-- Name: membership_removal_requests membership_removal_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT membership_removal_requests_pkey PRIMARY KEY (id);


--
-- Name: organization_invitations organization_invitations_organization_id_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_organization_id_email_key UNIQUE (organization_id, email);


--
-- Name: organization_invitations organization_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_pkey PRIMARY KEY (id);


--
-- Name: organization_members organization_members_organization_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_organization_id_user_id_key UNIQUE (organization_id, user_id);


--
-- Name: organization_members organization_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_pkey PRIMARY KEY (id);


--
-- Name: process_instances process_instances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.process_instances
    ADD CONSTRAINT process_instances_pkey PRIMARY KEY (id);


--
-- Name: processes processes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processes
    ADD CONSTRAINT processes_pkey PRIMARY KEY (id);


--
-- Name: relationships relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: schema_versions schema_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions
    ADD CONSTRAINT schema_versions_pkey PRIMARY KEY (id);


--
-- Name: schema_versions schema_versions_schema_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions
    ADD CONSTRAINT schema_versions_schema_id_version_key UNIQUE (schema_id, version);


--
-- Name: schemas schemas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schemas
    ADD CONSTRAINT schemas_pkey PRIMARY KEY (id);


--
-- Name: _hyper_1_1_chunk_events_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_events_timestamp_idx ON _timescaledb_internal._hyper_1_1_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_1_1_chunk_idx_events_data; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_data ON _timescaledb_internal._hyper_1_1_chunk USING gin (data);


--
-- Name: _hyper_1_1_chunk_idx_events_entity; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_entity ON _timescaledb_internal._hyper_1_1_chunk USING btree (entity_id, entity_type);


--
-- Name: _hyper_1_1_chunk_idx_events_metadata; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_metadata ON _timescaledb_internal._hyper_1_1_chunk USING gin (event_metadata);


--
-- Name: _hyper_1_1_chunk_idx_events_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_source ON _timescaledb_internal._hyper_1_1_chunk USING btree (source_node);


--
-- Name: _hyper_1_1_chunk_idx_events_timestamp; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_timestamp ON _timescaledb_internal._hyper_1_1_chunk USING btree ("timestamp");


--
-- Name: _hyper_1_1_chunk_idx_events_type; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_1_1_chunk_idx_events_type ON _timescaledb_internal._hyper_1_1_chunk USING btree (event_type);


--
-- Name: events_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX events_timestamp_idx ON public.events USING btree ("timestamp" DESC);


--
-- Name: idx_entities_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_active ON public.entities USING btree (is_active);


--
-- Name: idx_entities_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_name ON public.entities USING btree (name);


--
-- Name: idx_entities_organization; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_organization ON public.entities USING btree (organization_id);


--
-- Name: idx_entities_properties_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_properties_gin ON public.entities USING gin (properties);


--
-- Name: idx_entities_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_status ON public.entities USING btree (status);


--
-- Name: idx_entities_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_type ON public.entities USING btree (entity_type);


--
-- Name: idx_entities_type_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_type_org ON public.entities USING btree (entity_type, organization_id);


--
-- Name: idx_entities_type_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entities_type_status ON public.entities USING btree (entity_type, status);


--
-- Name: idx_events_data; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_data ON public.events USING gin (data);


--
-- Name: idx_events_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_entity ON public.events USING btree (entity_id, entity_type);


--
-- Name: idx_events_metadata; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_metadata ON public.events USING gin (event_metadata);


--
-- Name: idx_events_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_source ON public.events USING btree (source_node);


--
-- Name: idx_events_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_timestamp ON public.events USING btree ("timestamp");


--
-- Name: idx_events_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_type ON public.events USING btree (event_type);


--
-- Name: idx_experiment_trials_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment_trials_created_by ON public.experiment_trials USING btree (created_by);


--
-- Name: idx_experiment_trials_experiment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment_trials_experiment_id ON public.experiment_trials USING btree (experiment_id);


--
-- Name: idx_experiment_trials_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment_trials_status ON public.experiment_trials USING btree (status);


--
-- Name: idx_experiment_trials_trial_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_experiment_trials_trial_number ON public.experiment_trials USING btree (trial_number);


--
-- Name: idx_org_invitations_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invitations_email ON public.organization_invitations USING btree (email);


--
-- Name: idx_org_invitations_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invitations_expires ON public.organization_invitations USING btree (expires_at);


--
-- Name: idx_org_invitations_invited_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invitations_invited_by ON public.organization_invitations USING btree (invited_by);


--
-- Name: idx_org_invitations_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invitations_org_id ON public.organization_invitations USING btree (organization_id);


--
-- Name: idx_org_invitations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invitations_status ON public.organization_invitations USING btree (status);


--
-- Name: idx_org_members_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_members_active ON public.organization_members USING btree (is_active);


--
-- Name: idx_org_members_invited_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_members_invited_by ON public.organization_members USING btree (invited_by);


--
-- Name: idx_org_members_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_members_org_id ON public.organization_members USING btree (organization_id);


--
-- Name: idx_org_members_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_members_role ON public.organization_members USING btree (role);


--
-- Name: idx_org_members_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_members_user_id ON public.organization_members USING btree (user_id);


--
-- Name: idx_process_instances_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_instances_batch ON public.process_instances USING btree (batch_id);


--
-- Name: idx_process_instances_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_instances_started ON public.process_instances USING btree (started_at);


--
-- Name: idx_process_instances_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_process_instances_status ON public.process_instances USING btree (status);


--
-- Name: idx_processes_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_processes_created_by ON public.processes USING btree (created_by);


--
-- Name: idx_processes_organization; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_processes_organization ON public.processes USING btree (organization_id);


--
-- Name: idx_processes_template; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_processes_template ON public.processes USING btree (is_template);


--
-- Name: idx_rel_device_ownership; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_device_ownership ON public.relationships USING btree (from_entity, to_entity, relationship_type) WHERE ((relationship_type)::text = 'owns'::text);


--
-- Name: idx_rel_from; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_from ON public.relationships USING btree (from_entity);


--
-- Name: idx_rel_properties; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_properties ON public.relationships USING gin (properties);


--
-- Name: idx_rel_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_time ON public.relationships USING btree (valid_from, valid_to);


--
-- Name: idx_rel_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_to ON public.relationships USING btree (to_entity);


--
-- Name: idx_rel_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_type ON public.relationships USING btree (relationship_type);


--
-- Name: idx_removal_requests_approved_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_removal_requests_approved_by ON public.membership_removal_requests USING btree (approved_by);


--
-- Name: idx_removal_requests_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_removal_requests_org_id ON public.membership_removal_requests USING btree (organization_id);


--
-- Name: idx_removal_requests_requested_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_removal_requests_requested_by ON public.membership_removal_requests USING btree (requested_by);


--
-- Name: idx_removal_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_removal_requests_status ON public.membership_removal_requests USING btree (status);


--
-- Name: idx_removal_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_removal_requests_user_id ON public.membership_removal_requests USING btree (user_id);


--
-- Name: events ts_insert_blocker; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.events FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- Name: entities update_entities_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON public.entities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: entities fk_entities_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT fk_entities_organization FOREIGN KEY (organization_id) REFERENCES public.entities(id);


--
-- Name: experiment_trials fk_experiment_trials_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment_trials
    ADD CONSTRAINT fk_experiment_trials_created_by FOREIGN KEY (created_by) REFERENCES public.entities(id);


--
-- Name: experiment_trials fk_experiment_trials_experiment; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiment_trials
    ADD CONSTRAINT fk_experiment_trials_experiment FOREIGN KEY (experiment_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: organization_invitations fk_org_invitations_invited_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT fk_org_invitations_invited_by FOREIGN KEY (invited_by) REFERENCES public.entities(id);


--
-- Name: organization_invitations fk_org_invitations_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT fk_org_invitations_organization FOREIGN KEY (organization_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: organization_members fk_org_members_invited_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT fk_org_members_invited_by FOREIGN KEY (invited_by) REFERENCES public.entities(id);


--
-- Name: organization_members fk_org_members_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT fk_org_members_organization FOREIGN KEY (organization_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: organization_members fk_org_members_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT fk_org_members_user FOREIGN KEY (user_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: process_instances fk_process_instances_process; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.process_instances
    ADD CONSTRAINT fk_process_instances_process FOREIGN KEY (process_id) REFERENCES public.processes(id);


--
-- Name: processes fk_processes_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processes
    ADD CONSTRAINT fk_processes_created_by FOREIGN KEY (created_by) REFERENCES public.entities(id);


--
-- Name: processes fk_processes_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processes
    ADD CONSTRAINT fk_processes_organization FOREIGN KEY (organization_id) REFERENCES public.entities(id);


--
-- Name: relationships fk_relationships_from_entity; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT fk_relationships_from_entity FOREIGN KEY (from_entity) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: relationships fk_relationships_to_entity; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT fk_relationships_to_entity FOREIGN KEY (to_entity) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: membership_removal_requests fk_removal_requests_approved_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT fk_removal_requests_approved_by FOREIGN KEY (approved_by) REFERENCES public.entities(id);


--
-- Name: membership_removal_requests fk_removal_requests_organization; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT fk_removal_requests_organization FOREIGN KEY (organization_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: membership_removal_requests fk_removal_requests_requested_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT fk_removal_requests_requested_by FOREIGN KEY (requested_by) REFERENCES public.entities(id);


--
-- Name: membership_removal_requests fk_removal_requests_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_removal_requests
    ADD CONSTRAINT fk_removal_requests_user FOREIGN KEY (user_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: schema_versions fk_schema_versions_schema_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions
    ADD CONSTRAINT fk_schema_versions_schema_id FOREIGN KEY (schema_id) REFERENCES public.schemas(id);


--
-- PostgreSQL database dump complete
--

