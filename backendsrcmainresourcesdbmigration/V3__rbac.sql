-- V3__rbac.sql
-- User table with role-based access control
-- Author: Java Developer 2 - GANESH BS

CREATE TABLE app_user (
    id           BIGSERIAL PRIMARY KEY,
    username     VARCHAR(100) UNIQUE NOT NULL,
    password     VARCHAR(255)        NOT NULL,
    email        VARCHAR(150) UNIQUE,
    role         VARCHAR(50)         NOT NULL DEFAULT 'VIEWER',
    is_active    BOOLEAN             NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_username ON app_user(username);
CREATE INDEX idx_user_role     ON app_user(role);

-- Seed default admin account
-- Password is: Admin@123
-- BCrypt hash generated with strength 12
INSERT INTO app_user (username, password, email, role)
VALUES (
    'admin',
    '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYXW8kV7Jg.',
    'admin@company.com',
    'ADMIN'
);

-- Comments
COMMENT ON TABLE app_user IS 'Application users with role-based access';
COMMENT ON COLUMN app_user.role IS 'User role: ADMIN, MANAGER, VIEWER';
