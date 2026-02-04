SELECT * FROM reconx.users;
UPDATE users
SET status = 'active',
    failed_login_attempts = 0,
    account_locked_until = NULL
WHERE username = 'admin';