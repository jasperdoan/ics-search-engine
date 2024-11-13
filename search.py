# search.py

import json
import math
import time

from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

from utils.tokenizer import tokenize
from utils.constants import RANGE_DIR, DOCS_FILE
from utils.partials_handler import get_term_partial_path

@dataclass
class SearchResult:
    url: str
    score: float
    matched_terms: List[str]

class SearchEngine:
    def __init__(self):
        # Load document metadata
        with open(DOCS_FILE, 'r') as f:
            self.documents = json.load(f)
            
    def _load_term_postings(self, term: str) -> Dict:
        """Load postings for a specific term from its partial index"""
        partial_path = get_term_partial_path(term)
        try:
            with open(partial_path, 'r') as f:
                partial_index = json.load(f)
                return partial_index.get(term, {})
        except FileNotFoundError:
            return {}

    def _compute_query_vector(self, query_terms: List[str]) -> Dict[str, float]:
        """Compute normalized term frequencies for query terms"""
        query_vector = defaultdict(float)
        term_freq = defaultdict(int)
        
        # Count term frequencies
        for term in query_terms:
            term_freq[term] += 1
            
        # Normalize frequencies
        length = len(query_terms)
        if length > 0:
            for term, freq in term_freq.items():
                query_vector[term] = freq / length

        return query_vector

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        # Process query
        query_terms = list(set(tokenize(query)))
        if not query_terms:
            return []
            
        print(f"\nProcessing query terms: {query_terms}")
        
        # Track documents and their scores
        doc_scores: Dict[int, Tuple[float, set]] = defaultdict(lambda: (0.0, set()))
        
        # Calculate query vector
        query_vector = self._compute_query_vector(query_terms)
        
        # Process each query term
        for term in query_terms:
            # Load postings for this term
            postings = self._load_term_postings(term)
            if not postings:
                continue
                
            # Update document scores
            for doc_id, freq, imp, tf_idf in postings:
                score, terms = doc_scores[doc_id]
                doc_scores[doc_id] = (score + (tf_idf * query_vector[term]), terms | {term})
        
        # Filter for docs containing all terms (AND semantics)
        results = []
        for doc_id, (score, matched_terms) in doc_scores.items():
            if len(matched_terms) == len(query_terms):  # Must match all terms
                results.append(SearchResult(
                    url=self.documents[str(doc_id)]["url"],
                    score=score,
                    matched_terms=list(matched_terms)
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]

def main():
    search_engine = SearchEngine()
    
    while True:
        query = input("\nEnter search query (or 'quit' to exit): ").strip()
        if query.lower() == 'quit':
            break
            
        start_time = time.time()
        results = search_engine.search(query)
        end_time = time.time()
        
        if not results:
            print("No results found.")
            continue
            
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.url}")
            print(f"   Score: {result.score:.4f}")
        print(f"\nSearch completed in {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()