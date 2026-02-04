-- ReconX Banking Reconciliation System - Database Schema
-- MVP Level Implementation with Performance Optimizations

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS reconciliation_results;
DROP TABLE IF EXISTS internal_records;
DROP TABLE IF EXISTS bank_statements;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS mfa_secrets;
DROP TABLE IF EXISTS file_uploads;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

-- Roles Table
CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT
);

-- Users Table with Enhanced Security
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role_id INT NOT NULL,
    status ENUM('active', 'inactive', 'locked', 'pending_verification') DEFAULT 'pending_verification',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_required BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (updated_by) REFERENCES users(user_id),
    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_status (status),
    INDEX idx_users_role (role_id)
);

-- File Uploads Table - Track uploaded files
CREATE TABLE file_uploads (
    upload_id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type ENUM('bank_statement', 'internal_record', 'collection_report') NOT NULL,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    status ENUM('uploaded', 'processing', 'processed', 'error', 'deleted') DEFAULT 'uploaded',
    error_message TEXT,
    records_count INT DEFAULT 0,
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id),
    INDEX idx_file_uploads_user (uploaded_by),
    INDEX idx_file_uploads_status (status),
    INDEX idx_file_uploads_type (file_type),
    INDEX idx_file_uploads_date (uploaded_at),
    INDEX idx_file_uploads_filename (filename)
);

-- MFA Secrets Table
CREATE TABLE mfa_secrets (
    secret_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    secret_key VARCHAR(255) NOT NULL,
    backup_codes JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_mfa_user (user_id)
);

-- User Sessions Table
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_expires (expires_at),
    INDEX idx_sessions_token (token_hash)
);

-- Bank Statements Table with Enhanced Fields
CREATE TABLE bank_statements (
    statement_id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_date DATE NOT NULL,
    bank_ref VARCHAR(100) NOT NULL,
    description TEXT,
    currency VARCHAR(10) DEFAULT 'GHS',
    amount DECIMAL(18,2) NOT NULL,
    branch VARCHAR(100),
    account_number VARCHAR(50),
    transaction_type ENUM('credit', 'debit', 'transfer') DEFAULT 'credit',
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    status ENUM('uploaded', 'processing', 'processed', 'error') DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id),
    INDEX idx_bank_statements_date (transaction_date),
    INDEX idx_bank_statements_amount (amount),
    INDEX idx_bank_statements_ref (bank_ref),
    INDEX idx_bank_statements_uploaded_by (uploaded_by),
    INDEX idx_bank_statements_status (status),
    INDEX idx_bank_statements_currency (currency),
    INDEX idx_bank_statements_branch (branch),
    FULLTEXT idx_bank_statements_description (description)
);

-- Internal Records Table with Enhanced Fields
CREATE TABLE internal_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_date DATE NOT NULL,
    reference VARCHAR(100) NOT NULL,
    narration TEXT,
    currency VARCHAR(10) DEFAULT 'GHS',
    amount DECIMAL(18,2) NOT NULL,
    department VARCHAR(100),
    cost_center VARCHAR(100),
    transaction_type ENUM('income', 'expense', 'transfer', 'adjustment') DEFAULT 'expense',
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    status ENUM('uploaded', 'processing', 'processed', 'error') DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id),
    INDEX idx_internal_records_date (transaction_date),
    INDEX idx_internal_records_amount (amount),
    INDEX idx_internal_records_ref (reference),
    INDEX idx_internal_records_uploaded_by (uploaded_by),
    INDEX idx_internal_records_status (status),
    INDEX idx_internal_records_currency (currency),
    INDEX idx_internal_records_department (department),
    FULLTEXT idx_internal_records_narration (narration)
);

-- Reconciliation Runs Table
CREATE TABLE reconciliation_runs (
    run_id VARCHAR(100) PRIMARY KEY,
    user_id INT NOT NULL,
    bank_file_count INT DEFAULT 0,
    internal_file_count INT DEFAULT 0,
    total_transactions INT DEFAULT 0,
    matched_count INT DEFAULT 0,
    unmatched_count INT DEFAULT 0,
    difference_count INT DEFAULT 0,
    tolerance DECIMAL(18,2) DEFAULT 0.00,
    status ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    processing_time_seconds INT NULL,
    output_file_path VARCHAR(500),
    error_message TEXT,
    configuration JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_reconciliation_runs_user (user_id),
    INDEX idx_reconciliation_runs_status (status),
    INDEX idx_reconciliation_runs_date (started_at)
);

-- Reconciliation Results Table with Enhanced Tracking
CREATE TABLE reconciliation_results (
    result_id INT PRIMARY KEY AUTO_INCREMENT,
    reconciliation_run_id VARCHAR(100) NOT NULL,
    bank_statement_id INT,
    internal_record_id INT,
    status ENUM('matched', 'unmatched', 'difference', 'manual_review') NOT NULL,
    difference DECIMAL(18,2) DEFAULT 0.00,
    tolerance DECIMAL(18,2) DEFAULT 0.00,
    match_confidence DECIMAL(5,2) DEFAULT 0.00,
    match_criteria JSON,
    matched_by INT,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT NULL,
    reviewed_at TIMESTAMP NULL,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reconciliation_run_id) REFERENCES reconciliation_runs(run_id),
    FOREIGN KEY (bank_statement_id) REFERENCES bank_statements(statement_id),
    FOREIGN KEY (internal_record_id) REFERENCES internal_records(record_id),
    FOREIGN KEY (matched_by) REFERENCES users(user_id),
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id),
    INDEX idx_reconciliation_results_run_id (reconciliation_run_id),
    INDEX idx_reconciliation_results_status (status),
    INDEX idx_reconciliation_results_bank (bank_statement_id),
    INDEX idx_reconciliation_results_internal (internal_record_id),
    INDEX idx_reconciliation_results_matched_by (matched_by),
    INDEX idx_reconciliation_results_date (matched_at)
);

-- Audit Logs Table with Enhanced Tracking
CREATE TABLE audit_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    severity ENUM('info', 'warning', 'error', 'critical') DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    INDEX idx_audit_logs_user (user_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_resource (resource_type, resource_id),
    INDEX idx_audit_logs_severity (severity),
    INDEX idx_audit_logs_created_at (created_at),
    INDEX idx_audit_logs_ip (ip_address)
);

-- Insert default roles with permissions
INSERT INTO roles (role_name, description, permissions) VALUES
('admin', 'System Administrator - Full access to all features', 
 '{"users": ["create", "read", "update", "delete"], "files": ["create", "read", "update", "delete"], "reconciliation": ["create", "read", "update", "delete"], "audit": ["read"], "system": ["configure"]}'),
('finance_officer', 'Finance Officer - Can upload files and run reconciliation', 
 '{"files": ["create", "read"], "reconciliation": ["create", "read"], "reports": ["read"]}'),
('auditor', 'Auditor - Can view reports and audit logs', 
 '{"reports": ["read"], "audit": ["read"], "reconciliation": ["read"]}'),
('viewer', 'Viewer - Read-only access to reports', 
 '{"reports": ["read"]}');

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password_hash, full_name, email, role_id, status, mfa_enabled, mfa_required, created_by) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G', 'System Administrator', 'admin@reconx.com', 1, 'active', FALSE, FALSE, 1);

-- Create additional performance indexes
CREATE INDEX idx_bank_statements_composite ON bank_statements(transaction_date, amount, currency);
CREATE INDEX idx_internal_records_composite ON internal_records(transaction_date, amount, currency);
CREATE INDEX idx_reconciliation_results_composite ON reconciliation_results(reconciliation_run_id, status, matched_at);
CREATE INDEX idx_audit_logs_composite ON audit_logs(user_id, action, created_at);

-- Create views for common queries
CREATE VIEW v_reconciliation_summary AS
SELECT 
    rr.reconciliation_run_id,
    rr.status,
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
    'bank_statement' as file_type,
    COUNT(*) as total_files,
    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed_files,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_files,
    MAX(uploaded_at) as last_upload
FROM bank_statements
UNION ALL
SELECT 
    'internal_record' as file_type,
    COUNT(*) as total_files,
    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed_files,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_files,
    MAX(uploaded_at) as last_upload
FROM internal_records;
