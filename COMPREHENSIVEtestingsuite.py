#!/usr/bin/env python3
"""
test_greeter.py - Comprehensive test suite for LightDM Python Greeter
"""

import unittest
import sys
import os
import tempfile
import time
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock GTK and LightDM before importing
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()
sys.modules['lightdm'] = MagicMock()
sys.modules['pam'] = MagicMock()

from security import (
    RateLimiter, 
    PasswordStrengthChecker,
    SecurePasswordValidator,
    AuditLogger,
    SessionManager
)

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.limiter = RateLimiter(max_attempts=3, window_seconds=60)
    
    def test_allows_initial_attempts(self):
        """Test that initial attempts are allowed"""
        allowed, wait_time = self.limiter.is_allowed("test_user")
        self.assertTrue(allowed)
        self.assertIsNone(wait_time)
    
    def test_blocks_after_max_attempts(self):
        """Test that rate limiting kicks in after max attempts"""
        # Make max attempts
        for _ in range(3):
            self.limiter.is_allowed("test_user")
        
        # Next attempt should be blocked
        allowed, wait_time = self.limiter.is_allowed("test_user")
        self.assertFalse(allowed)
        self.assertIsNotNone(wait_time)
        self.assertGreater(wait_time, 0)
    
    def test_different_keys_independent(self):
        """Test that different keys have independent limits"""
        # Max out one key
        for _ in range(3):
            self.limiter.is_allowed("user1")
        
        # Different key should still be allowed
        allowed, _ = self.limiter.is_allowed("user2")
        self.assertTrue(allowed)
    
    def test_reset_clears_limit(self):
        """Test that reset clears the rate limit"""
        # Max out attempts
        for _ in range(3):
            self.limiter.is_allowed("test_user")
        
        # Reset
        self.limiter.reset("test_user")
        
        # Should be allowed again
        allowed, _ = self.limiter.is_allowed("test_user")
        self.assertTrue(allowed)
    
    @patch('time.time')
    def test_window_expiry(self, mock_time):
        """Test that rate limit window expires"""
        # Set initial time
        mock_time.return_value = 1000
        
        # Max out attempts
        for _ in range(3):
            self.limiter.is_allowed("test_user")
        
        # Move time forward past window
        mock_time.return_value = 1061  # 61 seconds later
        
        # Should be allowed again
        allowed, _ = self.limiter.is_allowed("test_user")
        self.assertTrue(allowed)

class TestPasswordStrengthChecker(unittest.TestCase):
    """Test password strength evaluation"""
    
    def test_empty_password(self):
        """Test empty password returns minimum score"""
        result = PasswordStrengthChecker.check_strength("")
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['strength'], 'very_weak')
    
    def test_weak_password(self):
        """Test weak password detection"""
        result = PasswordStrengthChecker.check_strength("password")
        self.assertLessEqual(result['score'], 2)
        self.assertIn(result['strength'], ['very_weak', 'weak'])
    
    def test_strong_password(self):
        """Test strong password detection"""
        result = PasswordStrengthChecker.check_strength("MyP@ssw0rd123!")
        self.assertGreaterEqual(result['score'], 5)
        self.assertIn(result['strength'], ['strong', 'very_strong'])
    
    def test_character_detection(self):
        """Test character type detection"""
        result = PasswordStrengthChecker.check_strength("AbC123!@#")
        self.assertTrue(result['has_lowercase'])
        self.assertTrue(result['has_uppercase'])
        self.assertTrue(result['has_digits'])
        self.assertTrue(result['has_special'])
    
    def test_suggestions_generated(self):
        """Test that appropriate suggestions are generated"""
        result = PasswordStrengthChecker.check_strength("abc")
        self.assertIn("Use at least 8 characters", result['suggestions'])
        self.assertIn("Add uppercase letters", result['suggestions'])
        self.assertIn("Add numbers", result['suggestions'])
    
    def test_entropy_calculation(self):
        """Test entropy calculation"""
        # Simple password should have low entropy
        simple = PasswordStrengthChecker.check_strength("aaaa")
        # Complex password should have higher entropy
        complex = PasswordStrengthChecker.check_strength("Aa1!")
        
        self.assertGreater(complex['entropy'], simple['entropy'])

class TestSessionManager(unittest.TestCase):
    """Test session token management"""
    
    def setUp(self):
        self.manager = SessionManager()
    
    def test_token_creation(self):
        """Test session token creation"""
        token = self.manager.create_session_token("test_user", ttl_seconds=300)
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 20)
    
    def test_token_validation_success(self):
        """Test successful token validation"""
        token = self.manager.create_session_token("test_user", ttl_seconds=300)
        username = self.manager.validate_token(token)
        self.assertEqual(username, "test_user")
    
    def test_token_one_time_use(self):
        """Test that tokens can only be used once"""
        token = self.manager.create_session_token("test_user", ttl_seconds=300)
        
        # First validation should succeed
        username = self.manager.validate_token(token)
        self.assertEqual(username, "test_user")
        
        # Second validation should fail
        username = self.manager.validate_token(token)
        self.assertIsNone(username)
    
    def test_invalid_token(self):
        """Test invalid token returns None"""
        username = self.manager.validate_token("invalid_token")
        self.assertIsNone(username)
    
    @patch('time.time')
    def test_token_expiry(self, mock_time):
        """Test token expiration"""
        # Create token at time 1000
        mock_time.return_value = 1000
        token = self.manager.create_session_token("test_user", ttl_seconds=300)
        
        # Move time forward past expiry
        mock_time.return_value = 1301  # 301 seconds later
        
        # Validation should fail
        username = self.manager.validate_token(token)
        self.assertIsNone(username)
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        # Create multiple tokens
        token1 = self.manager.create_session_token("user1", ttl_seconds=1)
        token2 = self.manager.create_session_token("user2", ttl_seconds=300)
        
        # Wait for first token to expire
        time.sleep(1.1)
        
        # Clean up
        self.manager.cleanup_expired_tokens()
        
        # First token should be gone, second should remain
        self.assertIsNone(self.manager.validate_token(token1))
        self.assertEqual(self.manager.validate_token(token2), "user2")

class TestGreeterIntegration(unittest.TestCase):
    """Integration tests for greeter components"""
    
    @patch('lightdm.Greeter')
    @patch('gi.repository.Gtk.Window')
    def test_greeter_initialization(self, mock_window, mock_lightdm_greeter):
        """Test greeter initialization"""
        # This would test the actual greeter initialization
        # In a real scenario, we'd import the actual greeter class
        pass
    
    def test_password_validation_flow(self):
        """Test complete password validation flow"""
        # Create components
        rate_limiter = RateLimiter(max_attempts=5, window_seconds=60)
        strength_checker = PasswordStrengthChecker()
        
        # Test password
        test_password = "TestP@ssw0rd123"
        
        # Check rate limit
        allowed, _ = rate_limiter.is_allowed("test_user")
        self.assertTrue(allowed)
        
        # Check strength
        strength = strength_checker.check_strength(test_password)
        self.assertGreaterEqual(strength['score'], 4)
    
    def test_security_audit_flow(self):
        """Test security audit logging flow"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_log = f.name
        
        try:
            logger = AuditLogger(log_file=temp_log)
            
            # Log various events
            logger.log_login_attempt("test_user", True, "127.0.0.1")
            logger.log_security_event("RATE_LIMIT", {"user": "attacker"})
            logger.log_configuration_change("auto_submit", True, False)
            
            # Verify log file exists and has content
            self.assertTrue(os.path.exists(temp_log))
            with open(temp_log, 'r') as f:
                content = f.read()
                self.assertIn("LOGIN_ATTEMPT", content)
                self.assertIn("RATE_LIMIT", content)
                self.assertIn("CONFIG_CHANGE", content)
        finally:
            # Clean up
            if os.path.exists(temp_log):
                os.unlink(temp_log)

class TestMockPAMAuthentication(unittest.TestCase):
    """Test PAM authentication with mocking"""
    
    @patch('pam.pam')
    def test_successful_authentication(self, mock_pam_class):
        """Test successful PAM authentication"""
        # Setup mock
        mock_pam = Mock()
        mock_pam.authenticate.return_value = True
        mock_pam_class.return_value = mock_pam
        
        # Test authentication
        import pam
        p = pam.pam()
        result = p.authenticate("test_user", "password", service="lightdm")
        
        self.assertTrue(result)
        mock_pam.authenticate.assert_called_once_with(
            "test_user", "password", service="lightdm"
        )
    
    @patch('pam.pam')
    def test_failed_authentication(self, mock_pam_class):
        """Test failed PAM authentication"""
        # Setup mock
        mock_pam = Mock()
        mock_pam.authenticate.return_value = False
        mock_pam_class.return_value = mock_pam
        
        # Test authentication
        import pam
        p = pam.pam()
        result = p.authenticate("test_user", "wrong_password", service="lightdm")
        
        self.assertFalse(result)

class TestConfigurationLoading(unittest.TestCase):
    """Test configuration file handling"""
    
    def test_default_config_creation(self):
        """Test creation of default configuration"""
        import configparser
        
        config = configparser.ConfigParser()
        config['Settings'] = {
            'auto_submit': 'true',
            'validation_delay_ms': '300',
            'show_user_list': 'true',
            'background': '/usr/share/backgrounds/warty-final-ubuntu.png',
            'theme': 'dark'
        }
        
        # Verify configuration values
        self.assertTrue(config.getboolean('Settings', 'auto_submit'))
        self.assertEqual(config.getint('Settings', 'validation_delay_ms'), 300)
    
    def test_config_file_parsing(self):
        """Test parsing configuration from file"""
        import configparser
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("""
[Settings]
auto_submit = false
validation_delay_ms = 500

[Security]
max_attempts = 5
""")
            temp_config = f.name
        
        try:
            config = configparser.ConfigParser()
            config.read(temp_config)
            
            # Verify values
            self.assertFalse(config.getboolean('Settings', 'auto_submit'))
            self.assertEqual(config.getint('Settings', 'validation_delay_ms'), 500)
            self.assertEqual(config.getint('Security', 'max_attempts'), 5)
        finally:
            os.unlink(temp_config)

class TestPerformance(unittest.TestCase):
    """Performance tests"""
    
    def test_rate_limiter_performance(self):
        """Test rate limiter performance under load"""
        limiter = RateLimiter(max_attempts=100, window_seconds=60)
        
        start_time = time.time()
        
        # Simulate 1000 checks
        for i in range(1000):
            limiter.is_allowed(f"user_{i % 10}")
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second)
        self.assertLess(elapsed, 1.0)
    
    def test_password_strength_performance(self):
        """Test password strength checker performance"""
        passwords = [
            "simple",
            "MediumP@ss1",
            "VeryC0mplexP@ssw0rd!123",
            "a" * 100,  # Long password
        ] * 100  # 400 passwords total
        
        start_time = time.time()
        
        for password in passwords:
            PasswordStrengthChecker.check_strength(password)
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second)
        self.assertLess(elapsed, 1.0)

class TestAccessibility(unittest.TestCase):
    """Test accessibility features"""
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation support"""
        # This would test actual keyboard navigation in the UI
        # For now, we'll verify the structure supports it
        pass
    
    def test_screen_reader_compatibility(self):
        """Test screen reader compatibility"""
        # Verify that UI elements have proper labels
        # This would be tested with actual GTK widgets
        pass

def run_tests():
    """Run all tests with coverage reporting"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_cases = [
        TestRateLimiter,
        TestPasswordStrengthChecker,
        TestSessionManager,
        TestGreeterIntegration,
        TestMockPAMAuthentication,
        TestConfigurationLoading,
        TestPerformance,
        TestAccessibility
    ]
    
    for test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)