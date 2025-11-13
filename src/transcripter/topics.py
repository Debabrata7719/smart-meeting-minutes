"""
Topic/Keyword Extraction Module

Extracts top keywords from transcript using TF-IDF or Counter.
Lightweight and optimized for 8GB RAM systems.
"""

import re
from collections import Counter
from typing import List


# Common English stopwords (lightweight, no external library needed)
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
    'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if',
    'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
    'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more',
    'very', 'after', 'words', 'long', 'than', 'first', 'been', 'call',
    'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get',
    'come', 'made', 'may', 'part', 'i', 'we', 'you', 'she', 'do',
    'can', 'could', 'should', 'would', 'may', 'might', 'must'
}


def extract_topics(transcript: str, top_n: int = 5) -> List[str]:
    """
    Extract top keywords/topics from transcript.
    
    Uses simple word frequency counting with stopword removal.
    Lightweight alternative to full TF-IDF for 8GB RAM systems.
    
    Args:
        transcript: The full transcript text
        top_n: Number of top topics to return (default: 5)
        
    Returns:
        List of top keywords/topics
    """
    if not transcript or not transcript.strip():
        return []
    
    # Clean transcript: lowercase and remove punctuation
    text = transcript.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into words
    words = text.split()
    
    # Filter out stopwords and very short words
    filtered_words = [
        word for word in words
        if len(word) > 3 and word not in STOPWORDS
    ]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get top N words
    top_words = word_counts.most_common(top_n)
    
    # Format as capitalized topics
    topics = [word.capitalize() for word, count in top_words if count > 0]
    
    return topics


def extract_topics_tfidf(transcript: str, top_n: int = 5) -> List[str]:
    """
    Extract top keywords using TF-IDF (requires sklearn).
    
    This is an alternative method that uses sklearn's TfidfVectorizer.
    Falls back to simple Counter method if sklearn is not available.
    
    Args:
        transcript: The full transcript text
        top_n: Number of top topics to return (default: 5)
        
    Returns:
        List of top keywords/topics
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Use TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=top_n * 2,  # Get more features for better selection
            stop_words='english',
            ngram_range=(1, 2),  # Include unigrams and bigrams
            min_df=1,
            max_df=0.95
        )
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform([transcript])
        
        # Get feature names and scores
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top N features
        top_indices = scores.argsort()[-top_n:][::-1]
        topics = [feature_names[i].title() for i in top_indices if scores[i] > 0]
        
        return topics[:top_n]
    
    except ImportError:
        # Fallback to simple Counter method
        return extract_topics(transcript, top_n)

