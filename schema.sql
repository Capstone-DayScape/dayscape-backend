-- Create user and set (fake) password
CREATE USER dayscape WITH PASSWORD 'password';

-- Create dayscape-dev database and switch to it. All commands after
-- this line will be repeated for 'dayscape-prod' db
CREATE DATABASE "dayscape-dev";
\c "dayscape-dev"

-- Example command to connect to this db:
-- PGPASSWORD=<password> psql -h <IP> -U dayscape -d dayscape-dev

-- For generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

GRANT SELECT, INSERT, UPDATE, DELETE ON trip TO "dayscape";
GRANT SELECT, INSERT, UPDATE, DELETE ON preference TO "dayscape";
