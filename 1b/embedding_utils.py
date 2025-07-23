import os
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from tqdm import tqdm
import os
import re
from datetime import datetime, timedelta

class DocumentAnalyzer:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = None):
        """
        Initialize the document analyzer with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use.
                       Will be loaded from local ./models/ directory if available.
            device: Device to run the model on ('cuda' or 'cpu'). Auto-detected if None.
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Check for local model first
        local_model_path = f"./models/{model_name}"
        if os.path.exists(local_model_path):
            print(f"Loading model from local: {local_model_path}")
            self.model = SentenceTransformer(local_model_path, device=self.device)
        else:
            print(f"Downloading model: {model_name}")
            self.model = SentenceTransformer(model_name, device=self.device)
            
        # Create models directory if it doesn't exist
        os.makedirs("./models", exist_ok=True)
        
        # Save the model locally for future use
        if not os.path.exists(local_model_path):
            print(f"Saving model locally to: {local_model_path}")
            self.model.save(local_model_path)
            
        # Travel-specific keywords for boosting
        self.travel_keywords = [
            'itinerary', 'accommodation', 'hotel', 'hostel', 'airbnb',
            'transportation', 'flight', 'train', 'bus', 'car rental',
            'activities', 'sightseeing', 'tour', 'attraction', 'landmark',
            'restaurant', 'cafe', 'dining', 'food', 'cuisine',
            'budget', 'cost', 'price', 'expense',
            'day trip', 'excursion', 'itinerary', 'schedule', 'plan',
            'local culture', 'tradition', 'custom', 'etiquette',
            'safety', 'tips', 'advice', 'recommendation'
        ]
        
        # Initialize cache for embeddings
        self.embedding_cache = {}
    
    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        return f"{hash(text) & 0xFFFFFFFFFFFFFFFF}"
    
    def get_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Get embeddings for a list of texts with caching.
        
        Args:
            texts: List of text strings to embed.
            batch_size: Batch size for processing.
            
        Returns:
            Numpy array of embeddings (num_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
            
        # Check cache first
        uncached_texts = []
        text_indices = []
        embeddings = np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.embedding_cache:
                embeddings[i] = self.embedding_cache[cache_key]
            else:
                uncached_texts.append(text)
                text_indices.append(i)
        
        # Process uncached texts in batches
        if uncached_texts:
            for i in tqdm(range(0, len(uncached_texts), batch_size), desc="Generating embeddings"):
                batch = uncached_texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=len(batch)
                )
                
                # Cache the new embeddings
                for j, (text, emb) in enumerate(zip(batch, batch_embeddings)):
                    cache_key = self._get_cache_key(text)
                    self.embedding_cache[cache_key] = emb
                    embeddings[text_indices[i + j]] = emb
        
        return embeddings
    
    def _extract_travel_dates(self, text: str) -> List[datetime]:
        """Extract dates from text that might be relevant for travel planning."""
        # This is a simplified version - you might want to use a more robust date parser
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:next|this)\s+(?:week|month|year|summer|winter|spring|fall|autumn)\b',
            r'\b(?:in|for)\s+(\d+)\s+(?:day|week|month|year)s?\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    # This is a simplified example - you'd want to properly parse the dates
                    date_str = match.group(0)
                    # Add to dates list (in a real implementation, you'd parse this properly)
                    dates.append(date_str)
                except (ValueError, IndexError):
                    continue
        
        return dates
    
    def _calculate_relevance_boost(self, section: Dict[str, Any], query: str) -> float:
        """Calculate a relevance boost based on section metadata and content."""
        boost = 1.0
        
        # Boost sections with travel-related keywords in title
        if 'title' in section:
            title = section['title'].lower()
            for keyword in self.travel_keywords:
                if keyword in title:
                    boost *= 1.2  # 20% boost for each matching keyword in title
        
        # Boost sections that appear to be about specific days of travel
        if 'text' in section and re.search(r'\b(?:day|day\s+\d+|itinerary|schedule)\b', section['text'], re.IGNORECASE):
            boost *= 1.3
            
        # Boost sections that mention specific locations or activities
        location_indicators = ['in ', 'at ', 'visit', 'see ', 'explore', 'tour', 'trip to']
        if 'text' in section and any(indicator in section['text'].lower() for indicator in location_indicators):
            boost *= 1.15
            
        return min(boost, 2.5)  # Cap the maximum boost
    
    def rank_sections(
        self,
        sections: List[Dict[str, Any]],
        query: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rank sections by relevance to the query with travel-specific optimizations.
        
        Args:
            sections: List of section dictionaries with 'text' key
            query: Query text to rank sections against
            top_n: Number of top sections to return
            
        Returns:
            List of top sections with added 'relevance_score' field
        """
        if not sections:
            return []
            
        # Prepare texts for embedding (combine title and text for better context)
        texts = []
        for section in sections:
            section_text = f"{section.get('title', '')} {section.get('text', '')}"
            # Add document title if available for better context
            if 'document' in section:
                section_text = f"Document about {section['document']}. {section_text}"
            texts.append(section_text)
        
        # Get embeddings
        text_embeddings = self.get_embeddings(texts)
        query_embedding = self.get_embeddings([query])[0]
        
        # Calculate cosine similarities
        similarities = util.cos_sim(
            torch.tensor(query_embedding).unsqueeze(0),
            torch.tensor(text_embeddings)
        )[0].numpy()
        
        # Add scores to sections and apply boosts
        scored_sections = []
        for i, section in enumerate(sections):
            section = section.copy()
            base_score = float(similarities[i])
            
            # Apply travel-specific relevance boosts
            boost = self._calculate_relevance_boost(section, query)
            boosted_score = base_score * boost
            
            section['relevance_score'] = round(boosted_score, 4)
            section['base_score'] = round(base_score, 4)
            section['boost_factor'] = round(boost, 2)
            
            scored_sections.append(section)
        
        # Sort by boosted score (descending)
        scored_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top N sections
        return scored_sections[:top_n]

# Global analyzer instance
_analyzer = None

def get_analyzer():
    """Get or create a global DocumentAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DocumentAnalyzer()
    return _analyzer

def rank_sections_by_relevance(
    sections: List[Dict[str, Any]],
    job_description: str,
    persona: str = "",
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Rank sections by their relevance to the job description and persona
    with travel-specific optimizations.
    
    Args:
        sections: List of section dictionaries with 'text' key
        job_description: Description of the analysis task
        persona: Description of the analyst's role/expertise
        top_n: Number of top sections to return
        
    Returns:
        List of top sections with added 'relevance_score' field
    """
    analyzer = get_analyzer()
    
    # Enhance the query with travel-specific context
    enhanced_query = (
        f"You are a travel planner. {persona}\n\n"
        f"Plan a trip with these requirements: {job_description}\n"
        "Focus on: itineraries, accommodations, transportation, activities, "
        "dining options, sightseeing spots, and local tips."
    )
    
    return analyzer.rank_sections(sections, enhanced_query, top_n=top_n)
