"""
Input sanitization utilities to prevent XSS and other injection attacks
"""
import bleach
import re
import html


class TextSanitizer:
    """Sanitizer for user-generated text content"""
    
    # HTML tags that are allowed (conservative whitelist)
    ALLOWED_TAGS = []  # No HTML tags allowed
    
    # Attributes allowed in tags
    ALLOWED_ATTRIBUTES = {}
    
    # Protocols allowed in URLs
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    # Maximum text length for comments (YouTube API typically has 10k limit)
    MAX_COMMENT_LENGTH = 5000
    
    # Patterns to detect and sanitize
    PATTERNS = {
        'script_tags': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        'style_tags': re.compile(r'<style[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL),
        'event_handlers': re.compile(r'on\w+\s*=', re.IGNORECASE),
    }
    
    @classmethod
    def clean_comment_text(cls, text: str) -> str:
        """
        Sanitize user comment text to prevent XSS attacks
        
        Args:
            text: Raw comment text from user/API
            
        Returns:
            Sanitized text safe for display
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > cls.MAX_COMMENT_LENGTH:
            text = text[:cls.MAX_COMMENT_LENGTH]
        
        # Remove null bytes
        text = text.replace('\0', '')
        
        # Use bleach to clean HTML
        text = bleach.clean(
            text,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            protocols=cls.ALLOWED_PROTOCOLS,
            strip=True  # Remove disallowed tags instead of escaping
        )
        
        # Remove script tags (defense in depth)
        for pattern_name, pattern in cls.PATTERNS.items():
            text = pattern.sub('', text)
        
        # Escape remaining HTML entities
        text = html.escape(text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def clean_user_input(cls, text: str, max_length: int = 200) -> str:
        """
        Sanitize general user input (names, titles, etc)
        
        Args:
            text: Raw user input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\0', '')
        
        # Clean with bleach (more restrictive than comments)
        text = bleach.clean(
            text,
            tags=[],
            attributes={},
            strip=True
        )
        
        # Escape HTML
        text = html.escape(text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def clean_url(cls, url: str) -> str:
        """
        Sanitize URL to prevent injection attacks
        
        Args:
            url: Raw URL
            
        Returns:
            Sanitized URL
        """
        if not url or not isinstance(url, str):
            return ""
        
        url = url.strip()
        
        # Only allow http/https
        if not url.lower().startswith(('http://', 'https://')):
            return ""
        
        # Limit length
        if len(url) > 2048:
            return ""
        
        # Escape special characters
        url = html.escape(url)
        
        return url


def sanitize_comment(text: str) -> str:
    """Convenience function to sanitize comment text"""
    return TextSanitizer.clean_comment_text(text)


def sanitize_input(text: str, max_length: int = 200) -> str:
    """Convenience function to sanitize user input"""
    return TextSanitizer.clean_user_input(text, max_length)


def sanitize_url(url: str) -> str:
    """Convenience function to sanitize URL"""
    return TextSanitizer.clean_url(url)
