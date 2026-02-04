"""
Security Tests for ReconX
Tests authentication, authorization, rate limiting, and security features
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.security import generate_password_hash

# Import the modules to test
from utils.security import (
    RateLimiter, rate_limit, validate_password, sanitize_input,
    validate_file_upload, generate_secure_filename, validate_email,
    validate_username, sanitize_sql_input, validate_reconciliation_config
)
from utils.api_responses import APIResponse, handle_exception
from config import config

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_allowed(self):
        """Test that requests within limit are allowed"""
        key = "test_ip_1"
        max_attempts = 3
        window_seconds = 60
        
        # First 3 attempts should be allowed
        for i in range(3):
            allowed, remaining = self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
            self.assertTrue(allowed)
            self.assertEqual(remaining, 0)
        
        # 4th attempt should be blocked
        allowed, remaining = self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
        self.assertFalse(allowed)
        self.assertGreater(remaining, 0)
    
    def test_rate_limit_window_reset(self):
        """Test that rate limit resets after window expires"""
        key = "test_ip_2"
        max_attempts = 2
        window_seconds = 1  # 1 second window
        
        # Use up attempts
        self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
        self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
        
        # Should be blocked
        allowed, _ = self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
        self.assertFalse(allowed)
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = self.rate_limiter.is_allowed(key, max_attempts, window_seconds)
        self.assertTrue(allowed)
    
    def test_get_remaining_attempts(self):
        """Test remaining attempts calculation"""
        key = "test_ip_3"
        max_attempts = 5
        
        # No attempts yet
        remaining = self.rate_limiter.get_remaining_attempts(key, max_attempts)
        self.assertEqual(remaining, 5)
        
        # After 2 attempts
        self.rate_limiter.is_allowed(key, max_attempts, 60)
        self.rate_limiter.is_allowed(key, max_attempts, 60)
        
        remaining = self.rate_limiter.get_remaining_attempts(key, max_attempts)
        self.assertEqual(remaining, 3)

class TestPasswordValidation(unittest.TestCase):
    """Test password validation functionality"""
    
    def test_valid_password(self):
        """Test that strong passwords pass validation"""
        valid_password = "StrongPass123!"
        is_valid, errors = validate_password(valid_password)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_weak_password_short(self):
        """Test that short passwords fail validation"""
        weak_password = "Abc1!"
        is_valid, errors = validate_password(weak_password)
        self.assertFalse(is_valid)
        self.assertIn("at least 8 characters", errors[0])
    
    def test_weak_password_no_uppercase(self):
        """Test that passwords without uppercase fail validation"""
        weak_password = "strongpass123!"
        is_valid, errors = validate_password(weak_password)
        self.assertFalse(is_valid)
        self.assertIn("uppercase letter", errors[0])
    
    def test_weak_password_no_lowercase(self):
        """Test that passwords without lowercase fail validation"""
        weak_password = "STRONGPASS123!"
        is_valid, errors = validate_password(weak_password)
        self.assertFalse(is_valid)
        self.assertIn("lowercase letter", errors[0])
    
    def test_weak_password_no_number(self):
        """Test that passwords without numbers fail validation"""
        weak_password = "StrongPass!"
        is_valid, errors = validate_password(weak_password)
        self.assertFalse(is_valid)
        self.assertIn("number", errors[0])
    
    def test_weak_password_no_special_char(self):
        """Test that passwords without special characters fail validation"""
        weak_password = "StrongPass123"
        is_valid, errors = validate_password(weak_password)
        self.assertFalse(is_valid)
        self.assertIn("special character", errors[0])

class TestInputSanitization(unittest.TestCase):
    """Test input sanitization functionality"""
    
    def test_sanitize_input_clean(self):
        """Test that clean input is not modified"""
        clean_input = "This is clean text"
        sanitized = sanitize_input(clean_input)
        self.assertEqual(sanitized, clean_input)
    
    def test_sanitize_input_html_tags(self):
        """Test that HTML tags are removed"""
        dirty_input = "<script>alert('xss')</script>Clean text"
        sanitized = sanitize_input(dirty_input)
        self.assertEqual(sanitized, "Clean text")
    
    def test_sanitize_input_dangerous_chars(self):
        """Test that dangerous characters are removed"""
        dirty_input = "Text with < > \" ' characters"
        sanitized = sanitize_input(dirty_input)
        self.assertEqual(sanitized, "Text with   characters")
    
    def test_sanitize_input_truncate(self):
        """Test that long input is truncated"""
        long_input = "A" * 2000
        sanitized = sanitize_input(long_input, max_length=1000)
        self.assertEqual(len(sanitized), 1000)
        self.assertTrue(sanitized.endswith("A"))

class TestFileUploadValidation(unittest.TestCase):
    """Test file upload validation"""
    
    def test_valid_file_upload(self):
        """Test that valid files pass validation"""
        filename = "test.xlsx"
        file_size = 1024 * 1024  # 1MB
        
        is_valid, errors = validate_file_upload(filename, file_size)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_file_extension(self):
        """Test that invalid file extensions fail validation"""
        filename = "test.exe"
        file_size = 1024
        
        is_valid, errors = validate_file_upload(filename, file_size)
        self.assertFalse(is_valid)
        self.assertIn("not allowed", errors[0])
    
    def test_file_too_large(self):
        """Test that oversized files fail validation"""
        filename = "test.xlsx"
        file_size = 100 * 1024 * 1024  # 100MB
        
        is_valid, errors = validate_file_upload(filename, file_size)
        self.assertFalse(is_valid)
        self.assertIn("exceeds maximum", errors[0])
    
    def test_filename_too_long(self):
        """Test that very long filenames fail validation"""
        filename = "a" * 300
        file_size = 1024
        
        is_valid, errors = validate_file_upload(filename, file_size)
        self.assertFalse(is_valid)
        self.assertIn("too long", errors[0])
    
    def test_suspicious_filename_patterns(self):
        """Test that suspicious filename patterns are detected"""
        suspicious_patterns = [
            "../../../etc/passwd",
            "C:\\Windows\\System32\\cmd.exe",
            "script.vbs",
            "malware.js"
        ]
        
        for filename in suspicious_patterns:
            is_valid, errors = validate_file_upload(filename, 1024)
            self.assertFalse(is_valid)
            self.assertIn("suspicious patterns", errors[0])

class TestEmailValidation(unittest.TestCase):
    """Test email validation"""
    
    def test_valid_emails(self):
        """Test that valid emails pass validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com"
        ]
        
        for email in valid_emails:
            self.assertTrue(validate_email(email))
    
    def test_invalid_emails(self):
        """Test that invalid emails fail validation"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@.com",
            "user..name@domain.com"
        ]
        
        for email in invalid_emails:
            self.assertFalse(validate_email(email))

class TestUsernameValidation(unittest.TestCase):
    """Test username validation"""
    
    def test_valid_usernames(self):
        """Test that valid usernames pass validation"""
        valid_usernames = [
            "john_doe",
            "user123",
            "admin.user",
            "test-user"
        ]
        
        for username in valid_usernames:
            is_valid, errors = validate_username(username)
            self.assertTrue(is_valid, f"Username '{username}' failed: {errors}")
    
    def test_invalid_usernames(self):
        """Test that invalid usernames fail validation"""
        invalid_usernames = [
            "ab",  # Too short
            "a" * 60,  # Too long
            ".username",  # Starts with dot
            "username.",  # Ends with dot
            "-username",  # Starts with hyphen
            "username-",  # Ends with hyphen
            "user@name",  # Invalid character
            "user name"   # Space
        ]
        
        for username in invalid_usernames:
            is_valid, errors = validate_username(username)
            self.assertFalse(is_valid, f"Username '{username}' should have failed")

class TestReconciliationConfigValidation(unittest.TestCase):
    """Test reconciliation configuration validation"""
    
    def test_valid_config(self):
        """Test that valid configuration passes validation"""
        tolerance = 0.50
        batch_size = 1000
        
        is_valid, errors = validate_reconciliation_config(tolerance, batch_size)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_tolerance(self):
        """Test that invalid tolerance values fail validation"""
        # Negative tolerance
        is_valid, errors = validate_reconciliation_config(-1.0, 1000)
        self.assertFalse(is_valid)
        self.assertIn("cannot be negative", errors[0])
        
        # Unreasonably high tolerance
        is_valid, errors = validate_reconciliation_config(2000000, 1000)
        self.assertFalse(is_valid)
        self.assertIn("unreasonably high", errors[0])
    
    def test_invalid_batch_size(self):
        """Test that invalid batch sizes fail validation"""
        # Zero batch size
        is_valid, errors = validate_reconciliation_config(0.0, 0)
        self.assertFalse(is_valid)
        self.assertIn("must be at least 1", errors[0])
        
        # Too large batch size
        is_valid, errors = validate_reconciliation_config(0.0, 15000)
        self.assertFalse(is_valid)
        self.assertIn("cannot exceed 10,000", errors[0])

class TestAPIResponses(unittest.TestCase):
    """Test API response utilities"""
    
    def test_success_response(self):
        """Test success response format"""
        data = {"id": 1, "name": "test"}
        response, status_code = APIResponse.success(data, "Operation successful")
        
        self.assertEqual(status_code, 200)
        response_data = json.loads(response.get_data(as_text=True))
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], "Operation successful")
        self.assertEqual(response_data['data'], data)
    
    def test_error_response(self):
        """Test error response format"""
        response, status_code = APIResponse.error("Something went wrong", "ERROR_CODE")
        
        self.assertEqual(status_code, 400)
        response_data = json.loads(response.get_data(as_text=True))
        
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], "Something went wrong")
        self.assertEqual(response_data['error_code'], "ERROR_CODE")
    
    def test_validation_error_response(self):
        """Test validation error response format"""
        errors = ["Field is required", "Invalid format"]
        response, status_code = APIResponse.validation_error(errors)
        
        self.assertEqual(status_code, 422)
        response_data = json.loads(response.get_data(as_text=True))
        
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error_code'], "VALIDATION_ERROR")
        self.assertEqual(response_data['details']['validation_errors'], errors)

class TestExceptionHandling(unittest.TestCase):
    """Test exception handling utilities"""
    
    def test_value_error_handling(self):
        """Test that ValueError returns validation error response"""
        error = ValueError("Invalid input")
        response, status_code = handle_exception(error, "test_endpoint")
        
        self.assertEqual(status_code, 422)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data['error_code'], "VALIDATION_ERROR")
    
    def test_key_error_handling(self):
        """Test that KeyError returns missing field error response"""
        error = KeyError("username")
        response, status_code = handle_exception(error, "test_endpoint")
        
        self.assertEqual(status_code, 400)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data['error_code'], "MISSING_FIELD")
    
    def test_file_not_found_handling(self):
        """Test that FileNotFoundError returns not found response"""
        error = FileNotFoundError("file.txt")
        response, status_code = handle_exception(error, "test_endpoint")
        
        self.assertEqual(status_code, 404)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data['error_code'], "NOT_FOUND")

if __name__ == '__main__':
    unittest.main()
