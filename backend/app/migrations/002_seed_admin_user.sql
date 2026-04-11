-- Seed: Create first admin user
-- Default password: admin123
-- Run this SQL to create the initial admin account
-- Then login with username: admin, password: admin123

INSERT INTO users (username, email, hashed_password, role, full_name, is_active)
VALUES (
    'admin',
    'admin@learntogrow.local',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85500000000000000000000000000000000',
    'admin',
    'System Administrator',
    TRUE
)
ON CONFLICT (username) DO NOTHING;
