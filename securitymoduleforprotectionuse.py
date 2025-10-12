#!/usr/bin/env python3
"""
security.py - Enhanced Security Module for LightDM Python Greeter
Provides additional security features including rate limiting, audit logging,
and secure password handling.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from threading import Lock
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security features for the greeter"""
    
    def __init__(self, config_path: str = "/etc/lightdm/python-greeter-security.db"):
        self.db_path = config_path
        self.lock = Lock()
        self.memory_cache = {}
        self._init_database()
        self._cleanup_old_records()
    
    def _init_database(self):
        """Initialize security database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Failed attempts tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failed_attempts (
                    username TEXT,
                    ip_address TEXT,
                    timestamp REAL,
                    attempt_count INTEGER,
                    PRIMARY KEY (username, ip_address)
                )
            """)
            
            # Audit log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    username TEXT,
                    action TEXT,
                    success BOOLEAN,
                    ip_address TEXT,
                    details TEXT
                )
            """)
            
            # Rate limiting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    key TEXT PRIMARY KEY,
                    count INTEGER,
                    window_start REAL,
                    last_update REAL
                )
            """)
            
            # Session tokens (for multi-factor auth)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_tokens (
                    token TEXT PRIMARY KEY,
                    username TEXT,
                    created REAL,
                    expires REAL,
                    used BOOLEAN DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def _cleanup_old_records(self):
        """Remove old records from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clean up old audit logs (keep 30 days)
            thirty_days_ago = time.time() - (30 * 24 * 3600)
            cursor.execute("DELETE FROM audit_log WHERE timestamp < ?", (thirty_days_ago,))
            
            # Clean up expired session tokens
            cursor.execute("DELETE FROM session_tokens WHERE expires < ?", (time.time(),))
            
            # Clean up old rate limit records
            one_hour_ago = time.time() - 3600
            cursor.execute("DELETE FROM rate_limits WHERE last_update < ?", (one_hour_ago,))
            
            conn.commit()

class RateLimiter:
    """Implements rate limiting for password validation attempts"""
    
    def __init__(self, max_attempts: int = 10, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}
        self.lock = Lock()
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if an attempt is allowed for the given key
        
        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        with self.lock:
            now = time.time()
            
            if key not in self.attempts:
                self.attempts[key] = {
                    'count': 1,
                    'window_start': now
                }
                return True, None
            
            record = self.attempts[key]
            window_elapsed = now - record['window_start']
            
            if window_elapsed >= self.window_seconds:
                # Reset window
                record['count'] = 1
                record['window_start'] = now
                return True, None
            
            if record['count'] >= self.max_attempts:
                # Rate limited
                seconds_remaining = self.window_seconds - window_elapsed
                return False, int(seconds_remaining)
            
            # Increment counter
            record['count'] += 1
            return True, None
    
    def reset(self, key: str):
        """Reset rate limit for a key"""
        with self.lock:
            if key in self.attempts:
                del self.attempts[key]

class PasswordStrengthChecker:
    """Evaluates password strength and provides feedback"""
    
    @staticmethod
    def check_strength(password: str) -> Dict[str, any]:
        """
        Check password strength and return detailed analysis
        
        Returns:
            Dictionary with strength metrics
        """
        result = {
            'score': 0,
            'length': len(password),
            'has_lowercase': False,
            'has_uppercase': False,
            'has_digits': False,
            'has_special': False,
            'is_common': False,
            'entropy': 0,
            'strength': 'very_weak',
            'suggestions': []
        }
        
        if not password:
            return result
        
        # Check character types
        result['has_lowercase'] = any(c.islower() for c in password)
        result['has_uppercase'] = any(c.isupper() for c in password)
        result['has_digits'] = any(c.isdigit() for c in password)
        result['has_special'] = any(not c.isalnum() for c in password)
        
        # Calculate score
        if result['length'] >= 8:
            result['score'] += 1
        if result['length'] >= 12:
            result['score'] += 1
        if result['has_lowercase']:
            result['score'] += 1
        if result['has_uppercase']:
            result['score'] += 1
        if result['has_digits']:
            result['score'] += 1
        if result['has_special']:
            result['score'] += 1
        
        # Calculate entropy
        charset_size = 0
        if result['has_lowercase']:
            charset_size += 26
        if result['has_uppercase']:
            charset_size += 26
        if result['has_digits']:
            charset_size += 10
        if result['has_special']:
            charset_size += 32
        
        if charset_size > 0:
            import math
            result['entropy'] = result['length'] * math.log2(charset_size)
        
        # Determine strength level
        if result['score'] <= 2:
            result['strength'] = 'very_weak'
        elif result['score'] <= 3:
            result['strength'] = 'weak'
        elif result['score'] <= 4:
            result['strength'] = 'fair'
        elif result['score'] <= 5:
            result['strength'] = 'strong'
        else:
            result['strength'] = 'very_strong'
        
        # Generate suggestions
        if result['length'] < 8:
            result['suggestions'].append("Use at least 8 characters")
        if not result['has_uppercase']:
            result['suggestions'].append("Add uppercase letters")
        if not result['has_digits']:
            result['suggestions'].append("Add numbers")
        if not result['has_special']:
            result['suggestions'].append("Add special characters")
        
        return result

class SecurePasswordValidator:
    """Secure password validation with timing attack protection"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_attempts=5, window_seconds=60)
        self.failed_attempts = {}
        self.lock = Lock()
    
    def validate_with_timing_protection(self, username: str, password: str, 
                                       actual_hash: bytes) -> bool:
        """
        Validate password with constant-time comparison
        
        Args:
            username: Username for rate limiting
            password: Password to validate
            actual_hash: The actual password hash to compare against
            
        Returns:
            True if password is valid, False otherwise
        """
        # Check rate limiting
        allowed, wait_time = self.rate_limiter.is_allowed(username)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {username}. Wait {wait_time} seconds.")
            return False
        
        # Hash the provided password
        provided_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            b'lightdm_greeter_salt',  # In production, use a random salt per user
            100000
        )
        
        # Constant-time comparison
        is_valid = hmac.compare_digest(provided_hash, actual_hash)
        
        if is_valid:
            self.rate_limiter.reset(username)
            with self.lock:
                if username in self.failed_attempts:
                    del self.failed_attempts[username]
        else:
            with self.lock:
                if username not in self.failed_attempts:
                    self.failed_attempts[username] = 0
                self.failed_attempts[username] += 1
        
        return is_valid

class AuditLogger:
    """Comprehensive audit logging for security events"""
    
    def __init__(self, log_file: str = "/var/log/lightdm/security-audit.log"):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Setup dedicated audit logger"""
        self.audit_logger = logging.getLogger("security_audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        
        # Format for audit logs
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.audit_logger.addHandler(handler)
    
    def log_login_attempt(self, username: str, success: bool, 
                          ip_address: str = None, details: str = None):
        """Log login attempt"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'LOGIN_ATTEMPT',
            'username': username,
            'success': success,
            'ip_address': ip_address or 'local',
            'details': details
        }
        
        self.audit_logger.info(json.dumps(event))
    
    def log_security_event(self, event_type: str, details: Dict):
        """Log general security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **details
        }
        
        self.audit_logger.warning(json.dumps(event))
    
    def log_configuration_change(self, setting: str, old_value: any, new_value: any):
        """Log configuration changes"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'CONFIG_CHANGE',
            'setting': setting,
            'old_value': str(old_value),
            'new_value': str(new_value)
        }
        
        self.audit_logger.info(json.dumps(event))

class SessionManager:
    """Manages secure session tokens for multi-factor authentication"""
    
    def __init__(self):
        self.tokens = {}
        self.lock = Lock()
    
    def create_session_token(self, username: str, ttl_seconds: int = 300) -> str:
        """
        Create a secure session token
        
        Args:
            username: Username for the session
            ttl_seconds: Time to live in seconds
            
        Returns:
            Secure random token
        """
        token = secrets.token_urlsafe(32)
        expires = time.time() + ttl_seconds
        
        with self.lock:
            self.tokens[token] = {
                'username': username,
                'created': time.time(),
                'expires': expires,
                'used': False
            }
        
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """
        Validate a session token
        
        Args:
            token: Token to validate
            
        Returns:
            Username if valid, None otherwise
        """
        with self.lock:
            if token not in self.tokens:
                return None
            
            session = self.tokens[token]
            
            # Check expiration
            if time.time() > session['expires']:
                del self.tokens[token]
                return None
            
            # Check if already used (one-time tokens)
            if session['used']:
                return None
            
            # Mark as used
            session['used'] = True
            
            return session['username']
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        with self.lock:
            now = time.time()
            expired = [
                token for token, session in self.tokens.items()
                if now > session['expires']
            ]
            
            for token in expired:
                del self.tokens[token]

class BiometricAuthenticator:
    """Stub for biometric authentication integration"""
    
    def __init__(self):
        self.available = self._check_availability()
    
    def _check_availability(self) -> Dict[str, bool]:
        """Check which biometric methods are available"""
        return {
            'fingerprint': self._check_fingerprint(),
            'face_recognition': self._check_face_recognition()
        }
    
    def _check_fingerprint(self) -> bool:
        """Check if fingerprint reader is available"""
        # Check for fprintd service
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-active', 'fprintd'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_face_recognition(self) -> bool:
        """Check if face recognition is available"""
        # Check for howdy or similar
        try:
            import subprocess
            result = subprocess.run(
                ['which', 'howdy'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def authenticate_fingerprint(self, username: str) -> bool:
        """Authenticate using fingerprint"""
        if not self.available['fingerprint']:
            return False
        
        # Implementation would integrate with fprintd
        logger.info(f"Fingerprint authentication requested for {username}")
        return False  # Stub
    
    def authenticate_face(self, username: str) -> bool:
        """Authenticate using face recognition"""
        if not self.available['face_recognition']:
            return False
        
        # Implementation would integrate with howdy
        logger.info(f"Face recognition requested for {username}")
        return False  # Stub

# Export main components
__all__ = [
    'SecurityManager',
    'RateLimiter',
    'PasswordStrengthChecker',
    'SecurePasswordValidator',
    'AuditLogger',
    'SessionManager',
    'BiometricAuthenticator'
]