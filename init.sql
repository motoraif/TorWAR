-- TorWAR Database Initialization
-- Create basic tables for the application

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    workload_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB,
    version INTEGER DEFAULT 1
);

-- Workloads table
CREATE TABLE IF NOT EXISTS workloads (
    id SERIAL PRIMARY KEY,
    workload_id VARCHAR(255) UNIQUE NOT NULL,
    workload_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cache table for storing temporary data
CREATE TABLE IF NOT EXISTS cache (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_workloads_workload_id ON workloads(workload_id);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at);
