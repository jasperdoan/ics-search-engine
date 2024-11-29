import numpy as np
import json

from typing import Dict, List, Tuple
from pathlib import Path


class HITS:
    def __init__(self, max_iterations: int = 20, threshold: float = 0.0001):
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.hub_scores: Dict[str, float] = {}
        self.auth_scores: Dict[str, float] = {}
        

    def build_adjacency_matrix(self, documents: Dict[str, Dict]) -> Tuple[np.ndarray, Dict[str, int]]:
        """Build adjacency matrix from document link structure"""
        # Create URL to index mapping
        urls = list({doc['url'] for doc in documents.values()})
        url_to_idx = {url: i for i, url in enumerate(urls)}
        
        # Initialize adjacency matrix
        n = len(urls)
        adj_matrix = np.zeros((n, n))
        
        # Fill adjacency matrix
        for doc in documents.values():
            if 'outgoing_links' in doc:
                from_idx = url_to_idx[doc['url']]
                for link in doc['outgoing_links']:
                    if link in url_to_idx:  # Only consider internal links
                        to_idx = url_to_idx[link]
                        adj_matrix[from_idx][to_idx] = 1
                        
        return adj_matrix, url_to_idx
        

    def compute_scores(self, documents: Dict[str, Dict]) -> None:
        """Compute HITS hub and authority scores"""
        # Build adjacency matrix
        adj_matrix, url_to_idx = self.build_adjacency_matrix(documents)
        n = len(url_to_idx)
        
        # Initialize scores
        hub_vector = np.ones(n) / n
        auth_vector = np.ones(n) / n
        
        # Power iteration
        for _ in range(self.max_iterations):
            # Update authority scores
            new_auth = adj_matrix.T @ hub_vector
            new_auth = new_auth / np.linalg.norm(new_auth, 1)
            
            # Update hub scores
            new_hub = adj_matrix @ new_auth
            new_hub = new_hub / np.linalg.norm(new_hub, 1)
            
            # Check convergence
            if (np.abs(new_auth - auth_vector) < self.threshold).all() and \
               (np.abs(new_hub - hub_vector) < self.threshold).all():
                break
                
            auth_vector = new_auth
            hub_vector = new_hub
        
        # Store scores mapped to URLs
        idx_to_url = {i: url for url, i in url_to_idx.items()}
        self.auth_scores = {idx_to_url[i]: score*10 for i, score in enumerate(auth_vector)}
        self.hub_scores = {idx_to_url[i]: score*10 for i, score in enumerate(hub_vector)}
        

    def save_scores(self, output_dir: Path) -> None:
        """Save computed scores to disk"""
        output_dir.mkdir(exist_ok=True)
        
        scores = {
            'authority_scores': self.auth_scores,
            'hub_scores': self.hub_scores
        }
        
        with open(output_dir / 'hits_scores.json', 'w') as f:
            json.dump(scores, f)
            
            
    def load_scores(self, output_dir: Path) -> None:
        """Load pre-computed scores from disk"""
        try:
            with open(output_dir / 'hits_scores.json', 'r') as f:
                scores = json.load(f)
                self.auth_scores = scores['authority_scores']
                self.hub_scores = scores['hub_scores']
        except FileNotFoundError:
            print("No pre-computed HITS scores found")