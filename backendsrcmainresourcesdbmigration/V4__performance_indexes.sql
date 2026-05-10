-- V4__performance_indexes.sql
-- Additional performance optimization indexes

-- Index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_filing_created_at 
    ON regulatory_filing(created_at DESC);

-- Index on title (lowercase) for case-insensitive search
CREATE INDEX IF NOT EXISTS idx_filing_title_lower 
    ON regulatory_filing(LOWER(title));

-- Partial index for active pending filings
CREATE INDEX IF NOT EXISTS idx_filing_active_pending
    ON regulatory_filing(status, deadline_date)
    WHERE is_deleted = FALSE AND status = 'PENDING';