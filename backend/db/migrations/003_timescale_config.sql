-- Set up data retention policy (optional)
SELECT add_retention_policy('events', INTERVAL '2 years'); 