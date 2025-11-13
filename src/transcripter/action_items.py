"""
Action Item Extraction Module

Extracts action items from transcript text using rule-based NLP.
Lightweight and optimized for 8GB RAM systems.
"""

import re
from typing import List


def extract_action_items(transcript: str) -> List[str]:
    """
    Extract action items from transcript text.
    
    Detects sentences with action-oriented keywords and returns
    a clean list of action items formatted as bullet points.
    
    Args:
        transcript: The full transcript text
        
    Returns:
        List of action items formatted as "- [action item]"
    """
    if not transcript or not transcript.strip():
        return []
    
    # Clean transcript
    transcript = re.sub(r'\s+', ' ', transcript).strip()
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
    
    # Action item keywords and patterns
    action_keywords = [
        r'\bwill\b',
        r'\bshould\b',
        r'\bneed to\b',
        r'\bhave to\b',
        r'\brequired\b',
        r'\bassigned\b',
        r'\bresponsible\b',
        r'\bdeadline\b',
        r'\btask\b',
        r'\bgoing to\b',
        r'\bmust\b',
        r'\bplan to\b',
        r'\bpromised\b',
        r'\bcommit\b',
        r'\baction\b',
        r'\bdeliver\b',
        r'\bcomplete\b',
        r'\bfinish\b',
        r'\bdo\b',
        r'\bimplement\b',
    ]
    
    # Combine all patterns
    action_pattern = re.compile('|'.join(action_keywords), re.IGNORECASE)
    
    action_items = []
    seen_items = set()
    
    for sentence in sentences:
        # Skip very short sentences
        if len(sentence) < 15:
            continue
        
        # Check if sentence contains action keywords
        if action_pattern.search(sentence):
            # Clean up the sentence
            cleaned = sentence.strip()
            
            # Remove leading/trailing punctuation issues
            cleaned = re.sub(r'^[^\w]+', '', cleaned)
            cleaned = re.sub(r'[^\w]+$', '', cleaned)
            
            # Ensure proper capitalization
            if cleaned and not cleaned[0].isupper():
                cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
            
            # Skip duplicates (using first 50 chars as key)
            item_key = cleaned.lower()[:50]
            if item_key in seen_items:
                continue
            seen_items.add(item_key)
            
            # Format as bullet point
            action_items.append(f"- {cleaned}")
    
    # Limit to reasonable number (top 20)
    return action_items[:20]

