-- Function to validate JSON data against a schema
CREATE OR REPLACE FUNCTION validate_against_schema(
    data jsonb,
    schema_id varchar
) RETURNS boolean AS $$
DECLARE
    schema_def jsonb;
    required_fields text[];
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
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT validate_against_schema(
--     '{
--         "timestamp": "2024-03-19T08:00:00Z",
--         "value": 25.5,
--         "unit": "celsius",
--         "sensorType": "temperature",
--         "quality": "good",
--         "batteryLevel": 95
--     }'::jsonb,
--     'sensor.reading.v1'
-- ); 