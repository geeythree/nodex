"""
Security utilities for input validation and sanitization
"""

import re
import os
from typing import List, Optional
import logging
import html

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles security-related operations"""
    
    # Maximum allowed input lengths
    MAX_TEXT_LENGTH = 10000
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Patterns that might indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # Eval statements
        r'__proto__',  # Prototype pollution
        r'constructor\s*\[',  # Constructor access
        r'\$\{.*\}',  # Template literals that might be evaluated
    ]
    
    @staticmethod
    def sanitize_text_input(text: str) -> str:
        """
        Sanitize text input to prevent injection attacks
        
        Args:
            text: Raw text input
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If input is invalid or potentially malicious
        """
        if not text:
            raise ValueError("Text input cannot be empty")
        
        if len(text) > SecurityManager.MAX_TEXT_LENGTH:
            raise ValueError(f"Text input exceeds maximum length of {SecurityManager.MAX_TEXT_LENGTH} characters")
        
        # HTML escape the input
        sanitized = html.escape(text)
        
        # Check for suspicious patterns
        for pattern in SecurityManager.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in input: {pattern}")
                # Remove the suspicious content instead of rejecting entirely
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Remove any null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Limit consecutive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_image_data(image_data: str) -> bool:
        """
        Validate base64 image data
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            True if valid, False otherwise
        """
        # Check if it's a valid base64 data URL
        if not image_data.startswith('data:image/'):
            return False
        
        # Extract the base64 portion
        try:
            header, data = image_data.split(',', 1)
            # Rough size check (base64 is ~1.33x the original size)
            estimated_size = len(data) * 0.75
            if estimated_size > SecurityManager.MAX_IMAGE_SIZE:
                logger.warning(f"Image size ({estimated_size} bytes) exceeds maximum allowed size")
                return False
        except ValueError:
            return False
        
        # Check for valid image MIME types
        valid_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
        if not any(mime in header for mime in valid_types):
            logger.warning(f"Invalid image MIME type in header: {header}")
            return False
        
        return True
    
    @staticmethod
    def sanitize_domain(domain: str) -> str:
        """
        Sanitize domain input to ensure it's valid
        
        Args:
            domain: Domain string
            
        Returns:
            Sanitized domain
        """
        valid_domains = ['hr', 'sales', 'finance', 'operations', 'it', 'general', 'healthcare', 'creator']
        
        domain_lower = domain.lower().strip()
        if domain_lower not in valid_domains:
            logger.warning(f"Invalid domain '{domain}', defaulting to 'general'")
            return 'general'
        
        return domain_lower
    
    @staticmethod
    def get_cors_origins() -> List[str]:
        """
        Get CORS allowed origins from environment or use defaults
        
        Returns:
            List of allowed origins
        """
        env_origins = os.getenv('CORS_ORIGINS', '')
        
        if env_origins:
            # Parse comma-separated origins from environment
            origins = [origin.strip() for origin in env_origins.split(',')]
        else:
            # Default origins for development
            origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]
        
        # In production, never use wildcard
        if os.getenv('ENVIRONMENT', 'development') == 'production':
            # Remove any wildcards
            origins = [o for o in origins if o != '*']
            if not origins:
                logger.warning("No CORS origins configured for production!")
                origins = ["https://secureai.example.com"]  # Default production domain
        
        return origins
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> bool:
        """
        Validate API key (placeholder for actual implementation)
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not api_key:
            return False
        
        # In production, this would check against a database or auth service
        # For now, we'll check against environment variable
        valid_keys = os.getenv('API_KEYS', '').split(',')
        valid_keys = [k.strip() for k in valid_keys if k.strip()]
        
        return api_key in valid_keys if valid_keys else True  # Allow all in dev if no keys configured