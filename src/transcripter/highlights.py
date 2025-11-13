"""
Highlights Extraction Module

Extracts 5-7 meaningful sentences from transcript based on keyword scoring.
Lightweight and optimized for 8GB RAM systems.
"""

import re
from typing import List


def extract_highlights(transcript: str, max_highlights: int = 7) -> List[str]:
    """
    Extract meaningful highlights from transcript.
    
    Selects sentences based on importance keywords and returns
    them as a bullet points list.
    
    Args:
        transcript: The full transcript text
        max_highlights: Maximum number of highlights to return (default: 7)
        
    Returns:
        List of highlight sentences formatted as "- [highlight]"
    """
    if not transcript or not transcript.strip():
        return []
    
    # Clean transcript
    transcript = re.sub(r'\s+', ' ', transcript).strip()
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
    
    # Importance keywords for scoring
    importance_keywords = [
        r'\bdiscussed\b',
        r'\bdecided\b',
        r'\bimportant\b',
        r'\bkey point\b',
        r'\bsummary\b',
        r'\bdecision\b',
        r'\bagreed\b',
        r'\bapproval\b',
        r'\bannounced\b',
        r'\bconclusion\b',
        r'\bfinal\b',
        r'\bmain\b',
        r'\bprimary\b',
        r'\bcritical\b',
        r'\bsignificant\b',
        r'\bmajor\b',
    ]
    
    # Combine patterns
    importance_pattern = re.compile('|'.join(importance_keywords), re.IGNORECASE)
    
    # Score sentences
    scored_sentences = []
    for sentence in sentences:
        # Skip very short or very long sentences
        if len(sentence) < 20 or len(sentence) > 300:
            continue
        
        # Calculate score based on keyword matches
        matches = len(importance_pattern.findall(sentence))
        if matches > 0:
            # Bonus for sentence length (prefer medium-length sentences)
            length_score = 1.0 if 50 <= len(sentence) <= 200 else 0.5
            total_score = matches * length_score
            scored_sentences.append((total_score, sentence))
    
    # Sort by score (descending) and take top N
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s[1] for s in scored_sentences[:max_highlights]]
    
    # If we don't have enough, add some random meaningful sentences
    if len(top_sentences) < max_highlights:
        remaining = [s for s in sentences if s not in top_sentences and 30 <= len(s) <= 250]
        needed = max_highlights - len(top_sentences)
        top_sentences.extend(remaining[:needed])
    
    # Format as bullet points
    highlights = []
    seen = set()
    for sentence in top_sentences:
        # Clean up
        cleaned = sentence.strip()
        if not cleaned:
            continue
        
        # Remove leading/trailing punctuation issues
        cleaned = re.sub(r'^[^\w]+', '', cleaned)
        cleaned = re.sub(r'[^\w]+$', '', cleaned)
        
        # Ensure proper capitalization
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        
        # Skip duplicates
        item_key = cleaned.lower()[:50]
        if item_key in seen:
            continue
        seen.add(item_key)
        
        highlights.append(f"- {cleaned}")
    
    return highlights

