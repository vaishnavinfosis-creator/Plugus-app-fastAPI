"""
Content Moderation Service
Implements profanity filtering and inappropriate content detection
"""
import re
from typing import Tuple, List


class ContentModerator:
    """Content moderation for user-generated content"""
    
    # Basic profanity list (expandable)
    PROFANITY_PATTERNS = [
        r'\b(fuck|shit|damn|bitch|ass|bastard|crap|piss|dick|cock|pussy|cunt|whore|slut)\b',
        r'\b(idiot|stupid|dumb|moron|retard)\b',
        # Add more patterns as needed
    ]
    
    # Inappropriate content patterns
    INAPPROPRIATE_PATTERNS = [
        r'(https?://\S+)',  # URLs (potential spam)
        r'(\b\d{3}[-.]?\d{3}[-.]?\d{4}\b)',  # Phone numbers
        r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)',  # Email addresses
        r'(\b(buy|sell|discount|offer|promo|click here|visit)\b.*\b(now|today|limited)\b)',  # Spam patterns
    ]
    
    def __init__(self):
        """Initialize content moderator with compiled patterns"""
        self.profanity_regex = re.compile(
            '|'.join(self.PROFANITY_PATTERNS),
            re.IGNORECASE
        )
        self.inappropriate_regex = re.compile(
            '|'.join(self.INAPPROPRIATE_PATTERNS),
            re.IGNORECASE
        )
    
    def check_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check content for profanity and inappropriate content
        
        Args:
            text: Content to check
            
        Returns:
            Tuple of (is_flagged, reasons)
            - is_flagged: True if content should be flagged for moderation
            - reasons: List of reasons why content was flagged
        """
        if not text:
            return False, []
        
        reasons = []
        
        # Check for profanity
        profanity_matches = self.profanity_regex.findall(text)
        if profanity_matches:
            reasons.append(f"Contains profanity: {', '.join(set(profanity_matches))}")
        
        # Check for inappropriate content
        inappropriate_matches = self.inappropriate_regex.findall(text)
        if inappropriate_matches:
            # Flatten matches (some patterns return tuples)
            flat_matches = []
            for match in inappropriate_matches:
                if isinstance(match, tuple):
                    flat_matches.extend([m for m in match if m])
                else:
                    flat_matches.append(match)
            
            if flat_matches:
                reasons.append(f"Contains inappropriate content: {', '.join(flat_matches[:3])}")  # Limit to 3 examples
        
        # Check for excessive caps (potential shouting/spam)
        if len(text) > 20:  # Only check if text is long enough
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.5:
                reasons.append("Excessive use of capital letters")
        
        # Check for repeated characters (potential spam)
        if re.search(r'(.)\1{4,}', text):  # 5 or more repeated characters
            reasons.append("Contains repeated characters (potential spam)")
        
        is_flagged = len(reasons) > 0
        return is_flagged, reasons
    
    def sanitize_content(self, text: str) -> str:
        """
        Sanitize content by removing/replacing inappropriate elements
        
        Args:
            text: Content to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return text
        
        # Replace profanity with asterisks
        sanitized = self.profanity_regex.sub(lambda m: '*' * len(m.group()), text)
        
        # Remove URLs
        sanitized = re.sub(r'https?://\S+', '[URL removed]', sanitized)
        
        # Remove email addresses
        sanitized = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[Email removed]',
            sanitized
        )
        
        # Remove phone numbers
        sanitized = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[Phone removed]',
            sanitized
        )
        
        return sanitized


# Global instance
content_moderator = ContentModerator()
