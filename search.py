import json
import time
import pickle
import numpy as np

from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from urllib.parse import urldefrag
from hits import HITS

from utils.tokenizer import tokenize
from utils.constants import RANGE_DIR, DOCS_FILE, INDEX_MAP_FILE, INDEX_PEEK_FILE, FULL_ANALYTICS_DIR


@dataclass
class SearchResult:
    url: str
    score: float
    matched_terms: List[str]


class FileHandler:
    """Handles file operations for search"""
    
    def __init__(self, index_path: str, seek_index_path: str):
        self.index_path = Path(index_path)
        self.seek_index_path = Path(seek_index_path)
        self.file_ptr = None
        self.seek_positions: Dict[str, int] = {}

    def __enter__(self):
        self.file_ptr = open(self.index_path, "rb")  # Open in binary mode
        with open(self.seek_index_path, "r") as f:
            self.seek_positions = json.load(f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_ptr:
            self.file_ptr.close()

    def get_postings(self, term: str) -> List:
        """Get postings list for a term using seek position"""
        if term not in self.seek_positions:
            return []
            
        seek_val = self.seek_positions[term]
        self.file_ptr.seek(seek_val)
        return pickle.load(self.file_ptr)


class SearchEngine:
    def __init__(self):
        with open(DOCS_FILE, 'r') as f:
            self.documents = json.load(f)
        self.hits = HITS()  # Initialize HITS
        self._load_hits_scores()


    def _load_hits_scores(self):
        """Load pre-computed HITS scores"""
        try:
            self.hits.load_scores(Path(FULL_ANALYTICS_DIR))
        except FileNotFoundError:
            print("Computing HITS scores...")
            self.hits.compute_scores(self.documents)
            self.hits.save_scores(Path(FULL_ANALYTICS_DIR))


    def _compute_query_freq_term(self, query_terms: List[str]) -> Dict[str, float]:
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

    def _compute_vectors(self, query_terms: List[str], doc_scores: Dict[int, Tuple[float, set]]) -> Tuple[np.ndarray, np.ndarray]:
        """Vectorized query and document vector computation"""
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

    def search(self, query: str, max_results: int, file_handler: FileHandler) -> List[SearchResult]:
        """Execute search query and return ranked results"""
        query_terms = tokenize(query, for_query=True)
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
            term_data = file_handler.get_postings(term)
            if not term_data:
                continue
            
            _, postings = term_data  # term_data is a tuple of (term, postings)
            
            for doc_id, freq, imp, tf_idf, _ in postings:
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
        
        # Combine scores and create results
        results = []
        for i, (doc_id, (tf_idf_score, matched_terms)) in enumerate(doc_scores.items()):
            url = self.documents[str(doc_id)]["url"]
            term_match_boost = len(matched_terms) / total_query_terms
            
            # Get HITS scores
            auth_score = self.hits.auth_scores.get(url, 0.0)
            hub_score = self.hits.hub_scores.get(url, 0.0)
            
            # Updated scoring formula
            combined_score = (
                0.15 * tf_idf_score + 
                0.15 * similarities[i] +
                0.40 * term_match_boost +
                0.15 * auth_score +
                0.15 * hub_score
            )

            results.append(
                SearchResult(
                    url=urldefrag(url)[0],
                    score=combined_score,
                    matched_terms=list(matched_terms)
                )
            )

        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]


def main():
    search_engine = SearchEngine()
    
    with FileHandler(INDEX_PEEK_FILE, INDEX_MAP_FILE) as fh:
        while True:
            query = input("\nEnter search query (or 'q' to exit): ").strip()
            if query.lower() == 'q':
                break
                
            start_time = time.time()
            results = search_engine.search(query, 10, fh)
            query_time = time.time() - start_time
            
            if not results:
                print("No results found.")
                continue
                
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.url}")
                print(f"   Score: {result.score:.4f}")
                print(f"   Matched terms: {result.matched_terms}")
            print(f"\nSearch completed in {query_time:.4f} seconds")


if __name__ == "__main__":
    main()