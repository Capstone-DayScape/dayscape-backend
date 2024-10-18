CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- For generating UUIDs

CREATE TABLE trip (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner VARCHAR(255) NOT NULL,
    name TEXT,
    viewers TEXT[] DEFAULT '{}',
    editors TEXT[] DEFAULT '{}',
    trip_data JSONB,
    CHECK (owner ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_trip_owner ON trip(owner);

CREATE TABLE preference (
    email VARCHAR(255) PRIMARY KEY,
    preferences_data JSONB,
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);
ALTER TABLE preference
ADD CONSTRAINT check_preferences_data_size
CHECK (octet_length(preferences_data::text) <= 2048);

GRANT INSERT, UPDATE, DELETE ON trip TO "dayscape-backend@moonlit-mesh-437320-t8.iam";
GRANT INSERT, UPDATE, DELETE ON preference TO "dayscape-backend@moonlit-mesh-437320-t8.iam";

-- The following will fail because of constraint on preference size
-- INSERT INTO preference (email, preferences_data)
-- VALUES (
--     'test@example.com',
--     ('{ "key": "' || repeat('a', 2049) || '"}')::jsonb
-- );
