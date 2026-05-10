-- V2__audit.sql
-- Audit Log Table for tracking all changes
-- Author: Java Developer 2 - GANESH BS

CREATE TABLE audit_log (
    id           BIGSERIAL PRIMARY KEY,
    entity_type  VARCHAR(100)  NOT NULL,
    entity_id    BIGINT        NOT NULL,
    action       VARCHAR(50)   NOT NULL,   -- CREATE, UPDATE, DELETE
    performed_by VARCHAR(150),
    old_value    TEXT,                      -- JSON snapshot before change
    new_value    TEXT,                      -- JSON snapshot after change
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Composite index for fast lookup by entity
CREATE INDEX idx_audit_entity 
    ON audit_log(entity_type, entity_id);

-- Index for querying by user
CREATE INDEX idx_audit_user 
    ON audit_log(performed_by);

-- Index for time-range queries
CREATE INDEX idx_audit_created 
    ON audit_log(created_at DESC);

-- Comments
COMMENT ON TABLE audit_log IS 'Audit trail of all changes to regulatory filings';
COMMENT ON COLUMN audit_log.action IS 'Type of action: CREATE, UPDATE, DELETE';
COMMENT ON COLUMN audit_log.old_value IS 'JSON snapshot of entity before change';
COMMENT ON COLUMN audit_log.new_value IS 'JSON snapshot of entity after change';