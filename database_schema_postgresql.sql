-- ReconX Banking Reconciliation System - PostgreSQL Schema for Supabase
-- Converted from MySQL - Production Ready with Performance Optimizations

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS reconciliation_results CASCADE;
DROP TABLE IF EXISTS internal_records CASCADE;
DROP TABLE IF EXISTS bank_statements CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS mfa_secrets CASCADE;
DROP TABLE IF EXISTS file_uploads CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Create ENUM types
CREATE TYPE role_name AS ENUM ('admin', 'finance_officer', 'auditor', 'viewer');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'locked', 'pending_verification');
CREATE TYPE file_type_enum AS ENUM ('bank_statement', 'internal_record', 'collection_report');
CREATE TYPE file_status_enum AS ENUM ('uploaded', 'processing', 'processed', 'error', 'deleted');
CREATE TYPE transaction_type_bank AS ENUM ('credit', 'debit', 'transfer');
CREATE TYPE transaction_type_internal AS ENUM ('income', 'expense', 'transfer', 'adjustment');
CREATE TYPE reconciliation_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
CREATE TYPE reconciliation_result_status AS ENUM ('matched', 'unmatched', 'difference', 'manual_review');
CREATE TYPE audit_severity AS ENUM ('info', 'warning', 'error', 'critical');

-- Roles Table
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT
);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Users Table with Enhanced Security
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role_id INT NOT NULL,
    status user_status DEFAULT 'pending_verification',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_required BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(user_id),
    updated_by INT REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role_id);

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- File Uploads Table - Track uploaded files
CREATE TABLE file_uploads (
    upload_id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type file_type_enum NOT NULL,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    status file_status_enum DEFAULT 'uploaded',
    error_message TEXT,
    records_count INT DEFAULT 0,
    uploaded_by INT NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_file_uploads_user ON file_uploads(uploaded_by);
CREATE INDEX idx_file_uploads_status ON file_uploads(status);
CREATE INDEX idx_file_uploads_type ON file_uploads(file_type);
CREATE INDEX idx_file_uploads_date ON file_uploads(uploaded_at);
CREATE INDEX idx_file_uploads_filename ON file_uploads(filename);

CREATE TRIGGER update_file_uploads_updated_at BEFORE UPDATE ON file_uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- MFA Secrets Table
CREATE TABLE mfa_secrets (
    secret_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    secret_key VARCHAR(255) NOT NULL,
    backup_codes JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP NULL
);

CREATE INDEX idx_mfa_user ON mfa_secrets(user_id);

-- User Sessions Table
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_sessions_token ON user_sessions(token_hash);

-- Bank Statements Table with Enhanced Fields
CREATE TABLE bank_statements (
    statement_id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,
    bank_ref VARCHAR(100) NOT NULL,
    description TEXT,
    currency VARCHAR(10) DEFAULT 'GHS',
    amount DECIMAL(18,2) NOT NULL,
    branch VARCHAR(100),
    account_number VARCHAR(50),
    transaction_type transaction_type_bank DEFAULT 'credit',
    uploaded_by INT NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    status file_status_enum DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bank_statements_date ON bank_statements(transaction_date);
CREATE INDEX idx_bank_statements_amount ON bank_statements(amount);
CREATE INDEX idx_bank_statements_ref ON bank_statements(bank_ref);
CREATE INDEX idx_bank_statements_uploaded_by ON bank_statements(uploaded_by);
CREATE INDEX idx_bank_statements_status ON bank_statements(status);
CREATE INDEX idx_bank_statements_currency ON bank_statements(currency);
CREATE INDEX idx_bank_statements_branch ON bank_statements(branch);
CREATE INDEX idx_bank_statements_composite ON bank_statements(transaction_date, amount, currency);

-- GIN index for full-text search on description
CREATE INDEX idx_bank_statements_description_gin ON bank_statements USING GIN (to_tsvector('english', description));

CREATE TRIGGER update_bank_statements_updated_at BEFORE UPDATE ON bank_statements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Internal Records Table with Enhanced Fields
CREATE TABLE internal_records (
    record_id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,
    reference VARCHAR(100) NOT NULL,
    narration TEXT,
    currency VARCHAR(10) DEFAULT 'GHS',
    amount DECIMAL(18,2) NOT NULL,
    department VARCHAR(100),
    cost_center VARCHAR(100),
    transaction_type transaction_type_internal DEFAULT 'expense',
    uploaded_by INT NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    status file_status_enum DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_internal_records_date ON internal_records(transaction_date);
CREATE INDEX idx_internal_records_amount ON internal_records(amount);
CREATE INDEX idx_internal_records_ref ON internal_records(reference);
CREATE INDEX idx_internal_records_uploaded_by ON internal_records(uploaded_by);
CREATE INDEX idx_internal_records_status ON internal_records(status);
CREATE INDEX idx_internal_records_currency ON internal_records(currency);
CREATE INDEX idx_internal_records_department ON internal_records(department);
CREATE INDEX idx_internal_records_composite ON internal_records(transaction_date, amount, currency);

-- GIN index for full-text search on narration
CREATE INDEX idx_internal_records_narration_gin ON internal_records USING GIN (to_tsvector('english', narration));

CREATE TRIGGER update_internal_records_updated_at BEFORE UPDATE ON internal_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Reconciliation Runs Table
CREATE TABLE reconciliation_runs (
    run_id VARCHAR(100) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    bank_file_count INT DEFAULT 0,
    internal_file_count INT DEFAULT 0,
    total_transactions INT DEFAULT 0,
    matched_count INT DEFAULT 0,
    unmatched_count INT DEFAULT 0,
    difference_count INT DEFAULT 0,
    tolerance DECIMAL(18,2) DEFAULT 0.00,
    status reconciliation_status DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    processing_time_seconds INT NULL,
    output_file_path VARCHAR(500),
    error_message TEXT,
    configuration JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reconciliation_runs_user ON reconciliation_runs(user_id);
CREATE INDEX idx_reconciliation_runs_status ON reconciliation_runs(status);
CREATE INDEX idx_reconciliation_runs_date ON reconciliation_runs(started_at);

CREATE TRIGGER update_reconciliation_runs_updated_at BEFORE UPDATE ON reconciliation_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Reconciliation Results Table with Enhanced Tracking
CREATE TABLE reconciliation_results (
    result_id SERIAL PRIMARY KEY,
    reconciliation_run_id VARCHAR(100) NOT NULL REFERENCES reconciliation_runs(run_id),
    bank_statement_id INT REFERENCES bank_statements(statement_id),
    internal_record_id INT REFERENCES internal_records(record_id),
    status reconciliation_result_status NOT NULL,
    difference DECIMAL(18,2) DEFAULT 0.00,
    tolerance DECIMAL(18,2) DEFAULT 0.00,
    match_confidence DECIMAL(5,2) DEFAULT 0.00,
    match_criteria JSONB,
    matched_by INT REFERENCES users(user_id),
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT REFERENCES users(user_id),
    reviewed_at TIMESTAMP NULL,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reconciliation_results_run_id ON reconciliation_results(reconciliation_run_id);
CREATE INDEX idx_reconciliation_results_status ON reconciliation_results(status);
CREATE INDEX idx_reconciliation_results_bank ON reconciliation_results(bank_statement_id);
CREATE INDEX idx_reconciliation_results_internal ON reconciliation_results(internal_record_id);
CREATE INDEX idx_reconciliation_results_matched_by ON reconciliation_results(matched_by);
CREATE INDEX idx_reconciliation_results_date ON reconciliation_results(matched_at);
CREATE INDEX idx_reconciliation_results_composite ON reconciliation_results(reconciliation_run_id, status, matched_at);

CREATE TRIGGER update_reconciliation_results_updated_at BEFORE UPDATE ON reconciliation_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit Logs Table with Enhanced Tracking
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255) REFERENCES user_sessions(session_id),
    severity audit_severity DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_ip ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_composite ON audit_logs(user_id, action, created_at);

-- Insert default roles with permissions
INSERT INTO roles (role_name, description, permissions) VALUES
('admin', 'System Administrator - Full access to all features', 
 '{"users": ["create", "read", "update", "delete"], "files": ["create", "read", "update", "delete"], "reconciliation": ["create", "read", "update", "delete"], "audit": ["read"], "system": ["configure"]}'::jsonb),
('finance_officer', 'Finance Officer - Can upload files and run reconciliation', 
 '{"files": ["create", "read"], "reconciliation": ["create", "read"], "reports": ["read"]}'::jsonb),
('auditor', 'Auditor - Can view reports and audit logs', 
 '{"reports": ["read"], "audit": ["read"], "reconciliation": ["read"]}'::jsonb),
('viewer', 'Viewer - Read-only access to reports', 
 '{"reports": ["read"]}'::jsonb);

-- Insert default admin user (password: admin123)
-- Using same hash as original: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G
INSERT INTO users (username, password_hash, full_name, email, role_id, status, mfa_enabled, mfa_required, created_by) VALUES
(1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G', 'System Administrator', 'admin@reconx.com', 1, 'active'::user_status, FALSE, FALSE, NULL);

-- Create views for common queries
CREATE VIEW v_reconciliation_summary AS
SELECT 
    rr.reconciliation_run_id,
    rr.status::TEXT,
    rr.started_at,
    rr.completed_at,
    rr.processing_time_seconds,
    rr.matched_count,
    rr.unmatched_count,
    rr.difference_count,
    u.username as run_by,
    rr.tolerance
FROM reconciliation_runs rr
JOIN users u ON rr.user_id = u.user_id;

CREATE VIEW v_file_upload_summary AS
SELECT 
    'bank_statement'::TEXT as file_type,
    COUNT(*) as total_files,
    (SELECT COUNT(*) FROM bank_statements WHERE status = 'processed') as processed_files,
    (SELECT COUNT(*) FROM bank_statements WHERE status = 'error') as error_files,
    (SELECT MAX(uploaded_at) FROM bank_statements) as last_upload
UNION ALL
SELECT 
    'internal_record'::TEXT as file_type,
    COUNT(*) as total_files,
    (SELECT COUNT(*) FROM internal_records WHERE status = 'processed') as processed_files,
    (SELECT COUNT(*) FROM internal_records WHERE status = 'error') as error_files,
    (SELECT MAX(uploaded_at) FROM internal_records) as last_upload
FROM internal_records;

-- Create functions for common operations

-- Function to get user reconciliation summary
CREATE OR REPLACE FUNCTION get_user_reconciliation_summary(p_user_id INT)
RETURNS TABLE (
    total_runs BIGINT,
    completed_runs BIGINT,
    pending_runs BIGINT,
    failed_runs BIGINT,
    total_matched BIGINT,
    total_unmatched BIGINT
) AS $$
SELECT
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'completed'::reconciliation_status) as completed_runs,
    COUNT(*) FILTER (WHERE status = 'pending'::reconciliation_status) as pending_runs,
    COUNT(*) FILTER (WHERE status = 'failed'::reconciliation_status) as failed_runs,
    COALESCE(SUM(matched_count), 0) as total_matched,
    COALESCE(SUM(unmatched_count), 0) as total_unmatched
FROM reconciliation_runs
WHERE user_id = p_user_id;
$$ LANGUAGE SQL;

-- Function to log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_user_id INT,
    p_action VARCHAR,
    p_resource_type VARCHAR,
    p_resource_id VARCHAR,
    p_details JSONB,
    p_ip_address VARCHAR,
    p_user_agent TEXT,
    p_session_id VARCHAR,
    p_severity audit_severity
)
RETURNS BIGINT AS $$
DECLARE
    v_log_id BIGINT;
BEGIN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent, session_id, severity)
    VALUES (p_user_id, p_action, p_resource_type, p_resource_id, p_details, p_ip_address, p_user_agent, p_session_id, p_severity)
    RETURNING log_id INTO v_log_id;
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security for sensitive data protection
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_results ENABLE ROW LEVEL SECURITY;

-- Create RLS Policy: Users can only view their own sessions
CREATE POLICY users_own_records ON users
    FOR SELECT USING (user_id = CURRENT_SETTING('app.current_user_id')::INT OR CURRENT_SETTING('app.is_admin', 't') = 'true');

-- Health check table for API validation
CREATE TABLE IF NOT EXISTS health_check (
    id SERIAL PRIMARY KEY,
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO health_check (message) VALUES ('Supabase PostgreSQL schema initialized successfully') ON CONFLICT DO NOTHING;

COMMIT;
