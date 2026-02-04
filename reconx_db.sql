SELECT * FROM reconx.users;

UPDATE users
SET password_hash = '$2b$12$wH1QwQwQwQwQwQwQwQwQwOQwQwQwQwQwQwQwQwQwQwQwQwQwQwQW',
    status = 'active',
    failed_login_attempts = 0,
    account_locked_until = NULL
WHERE username = 'testuser';