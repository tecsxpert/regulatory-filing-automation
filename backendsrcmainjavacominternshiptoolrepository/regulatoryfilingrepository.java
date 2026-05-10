-- V1__init.sql
-- Regulatory Filing Automation - Initial Schema
-- Author: Java Developer 2 - GANESH BS

-- Main regulatory filing table
CREATE TABLE regulatory_filing (
    id                BIGSERIAL PRIMARY KEY,
    title             VARCHAR(255)        NOT NULL,
    description       TEXT,
    status            VARCHAR(50)         NOT NULL DEFAULT 'PENDING',
    category          VARCHAR(100),
    filing_date       DATE,
    deadline_date     DATE,
    submitted_by      VARCHAR(150),
    
    -- AI-generated fields
    ai_description    TEXT,
    ai_category       VARCHAR(100),
    ai_confidence     DECIMAL(5,2),
    ai_recommendations TEXT,
    
    -- File attachment
    file_path         VARCHAR(500),
    
    -- Soft delete flag
    is_deleted        BOOLEAN             NOT NULL DEFAULT FALSE,
    
    -- Audit timestamps
    created_at        TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance on common queries
CREATE INDEX idx_filing_status 
    ON regulatory_filing(status) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_filing_category 
    ON regulatory_filing(category) 
    WHERE is_deleted = FALSE;

CREATE INDEX idx_filing_deadline 
    ON regulatory_filing(deadline_date) 
    WHERE is_deleted = FALSE AND deadline_date IS NOT NULL;

CREATE INDEX idx_filing_created 
    ON regulatory_filing(created_at DESC);

CREATE INDEX idx_filing_deleted 
    ON regulatory_filing(is_deleted);

-- Index for full-text search on title and description
CREATE INDEX idx_filing_search 
    ON regulatory_filing USING gin(to_tsvector('english', title || ' ' || COALESCE(description, ''))) 
    WHERE is_deleted = FALSE;

-- Comments for documentation
COMMENT ON TABLE regulatory_filing IS 'Main table storing all regulatory filing records';
COMMENT ON COLUMN regulatory_filing.status IS 'Filing status: PENDING, IN_PROGRESS, SUBMITTED, APPROVED, REJECTED';
COMMENT ON COLUMN regulatory_filing.ai_confidence IS 'AI prediction confidence score (0.00 to 1.00)';
COMMENT ON COLUMN regulatory_filing.is_deleted IS 'Soft delete flag - true if record is deleted';