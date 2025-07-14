-- Create database
CREATE DATABASE kpa_db;

-- Connect to the database
\c kpa_db;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create kpa_forms table
CREATE TABLE IF NOT EXISTS kpa_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(50) NOT NULL,
    employee_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    performance_period VARCHAR(50) NOT NULL,
    kpa_title VARCHAR(200) NOT NULL,
    kpa_description TEXT,
    target_value DECIMAL(10,2) NOT NULL,
    achieved_value DECIMAL(10,2) NOT NULL,
    weightage DECIMAL(5,2) NOT NULL,
    score DECIMAL(5,2),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX idx_kpa_forms_employee_id ON kpa_forms(employee_id);
CREATE INDEX idx_kpa_forms_department ON kpa_forms(department);
CREATE INDEX idx_kpa_forms_created_at ON kpa_forms(created_at);
CREATE INDEX idx_users_phone_number ON users(phone_number);

-- Insert default user for testing
INSERT INTO users (phone_number, password_hash) 
VALUES ('7760873976', encode(digest('to_share@123', 'sha256'), 'hex'))
ON CONFLICT (phone_number) DO NOTHING;

-- Insert sample KPA forms data
INSERT INTO kpa_forms (
    employee_id, employee_name, department, designation, 
    performance_period, kpa_title, kpa_description, 
    target_value, achieved_value, weightage, score, remarks, created_by
) VALUES 
(
    'EMP001', 'John Doe', 'IT', 'Software Developer',
    'Q1-2025', 'Code Quality Improvement', 
    'Improve code quality metrics and reduce technical debt',
    90.00, 85.00, 20.00, 18.89, 'Good performance overall',
    (SELECT id FROM users WHERE phone_number = '7760873976')
),
(
    'EMP002', 'Jane Smith', 'HR', 'HR Manager',
    'Q1-2025', 'Employee Satisfaction', 
    'Maintain high employee satisfaction scores',
    95.00, 92.00, 25.00, 24.21, 'Excellent achievement',
    (SELECT id FROM users WHERE phone_number = '7760873976')
),
(
    'EMP003', 'Mike Johnson', 'Sales', 'Sales Executive',
    'Q1-2025', 'Sales Target Achievement', 
    'Achieve quarterly sales targets',
    100000.00, 105000.00, 30.00, 31.50, 'Exceeded expectations',
    (SELECT id FROM users WHERE phone_number = '7760873976')
);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kpa_forms_updated_at 
    BEFORE UPDATE ON kpa_forms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();