import json
import time
import numpy as np

from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from functools import lru_cache

from utils.tokenizer import tokenize, query_tokenize
from utils.constants import RANGE_DIR, DOCS_FILE, RANGE_SPLITS
from utils.partials_handler import get_term_partial_path



@dataclass
class SearchResult:
    url: str
    score: float
    matched_terms: List[str]



class SearchEngine:
    def __init__(self):
        with open(DOCS_FILE, 'r') as f:
            self.documents = json.load(f)
        print("Preloading partial indexes...")
        self._preload_partials()    # Preload all partial indexes
        print("Done preloading partial indexes")


    def _preload_partials(self):    # THIS IS THE SECRET SAUCE, THIS IS THE MAGIC THAT WILL GET OUR SEARCHES < 300ms
        """Preload all partial indexes into cache"""
        ranges = ['misc'] + [f"{start}_{end}" for start, end in RANGE_SPLITS]
        for range_name in ranges:
            partial_path = f"{RANGE_DIR}/index_{range_name}.json"
            try:
                # This will populate the LRU cache
                self._load_term_postings(partial_path)
                print(f"Loaded {partial_path}")
            except FileNotFoundError:
                print(f"Warning: {partial_path} not found")


    @lru_cache(maxsize=1000)    # Cache partial index loads / kinda like memoization as given as example in the doc!!!
    def _load_term_postings(self, partial_path: str) -> Dict:
        """Load postings for a specific term from its partial index"""
        try:
            with open(partial_path, 'r') as f:
                partial_index = json.load(f)
                return partial_index
        except FileNotFoundError:
            return {}


    def _compute_query_freq_term(self, query_terms: List[str]) -> Dict[str, float]:
        """
        Compute normalized term frequencies for query terms
        This is to normalizes query term frequencies to avoid bias from repeated terms
        Any repeated term in the query will dominate scoring, and is skewed by repeatition. By normalizing:
            - Fair weighting of terms
            - Scale-independent scoring
            - More accurate relevance ranking
            - Resistance to keyword stuffing
        """
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


    def _compute_vectors(self, query_terms: List[str], doc_scores: Dict[int, Tuple[float, set]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Vectorized query and document vector computation
        Switched converting query and documents into sparse vectors for comparison (memory efficient, a lot faster computation)
        """
        # Get all terms and create mapping
        all_terms = list(set(query_terms) | {term for _, terms in doc_scores.values() for term in terms})
        term_to_idx = {term: idx for idx, term in enumerate(all_terms)}
        
        # Initialize sparse matrices
        n_terms = len(term_to_idx)
        n_docs = len(doc_scores)
        
        # Create query vector efficiently
        query_data = np.ones(len(query_terms))
        query_indices = [term_to_idx[term] for term in query_terms]
        query_indptr = np.array([0, len(query_terms)])
        query_vector = csr_matrix((query_data, query_indices, query_indptr), shape=(1, n_terms))
        
        # Create document vectors efficiently
        doc_data = []
        doc_indices = []
        doc_indptr = [0]
        
        for doc_id, (score, terms) in doc_scores.items():
            term_indices = [term_to_idx[term] for term in terms]
            term_scores = [score] * len(terms)
            doc_data.extend(term_scores)
            doc_indices.extend(term_indices)
            doc_indptr.append(len(doc_indices))
        doc_vectors = csr_matrix((doc_data, doc_indices, doc_indptr), shape=(n_docs, n_terms))
        
        return query_vector, doc_vectors


    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        query_terms = query_tokenize(query)
        if not query_terms:
            return []
            
        print(f"\nProcessing query terms: {query_terms}")
        
        # Track documents and their scores
        doc_scores: Dict[int, Tuple[float, set]] = defaultdict(lambda: (0.0, set()))
        
        # Calculate query vector 
        query_vector = self._compute_query_freq_term(query_terms)
        total_query_terms = len(query_terms)
        
        # Process each query term
        for term in query_terms:
            partial_path = get_term_partial_path(term)
            partial_index = self._load_term_postings(partial_path)
            postings = partial_index.get(term, {})
            if not postings:
                continue
                
            for doc_id, freq, imp, tf_idf in postings:
                score, terms = doc_scores[doc_id]
                # Add term match bonus based on % of query terms matched
                match_bonus = len(terms | {term}) / total_query_terms
                doc_scores[doc_id] = (
                    score + (tf_idf * query_vector[term]), 
                    terms | {term}
                )
        
        if not doc_scores:
            return []
            
        # Compute cosine similarity
        q_vec, doc_vecs = self._compute_vectors(query_terms, doc_scores)
        similarities = cosine_similarity(q_vec, doc_vecs)[0]
        
        # Combine tf-idf scores with cosine similarity
        results = []
        for i, (doc_id, (tf_idf_score, matched_terms)) in enumerate(doc_scores.items()):
            # Boost documents matching more query terms
            term_match_boost = len(matched_terms) / total_query_terms
            combined_score = (
                0.2 * tf_idf_score + 
                0.2 * similarities[i] +
                0.6 * term_match_boost  # Make queries with more matched terms are more relevant
            )
            results.append(
                SearchResult(
                    url=self.documents[str(doc_id)]["url"],
                    score=combined_score,
                    matched_terms=list(matched_terms)
                )
            )
        
        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]



def main():
    search_engine = SearchEngine()
    
    while True:
        query = input("\nEnter search query (or 'q' to exit): ").strip()
        if query.lower() == 'q':
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
            print(f"   Matched terms: {result.matched_terms}")
        print(f"\nSearch completed in {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()