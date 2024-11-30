import numpy as np

from typing import Dict, List, Tuple
from pathlib import Path


class PageRank:
    def __init__(self, damping_factor=0.85, max_iterations=100, threshold=0.0001):
        self.damping_factor = damping_factor
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.scores = {}
        

    def compute_scores(self, documents):
        # Build adjacency matrix
        urls = list({doc['url'] for doc in documents.values()})
        url_to_idx = {url: i for i, url in enumerate(urls)}
        n = len(urls)
        adj_matrix = np.zeros((n, n))
        
        # Fill matrix
        for doc in documents.values():
            if 'outgoing_links' in doc:
                from_idx = url_to_idx[doc['url']]
                outbound_count = len(doc['outgoing_links'])
                if outbound_count > 0:
                    for link in doc['outgoing_links']:
                        if link in url_to_idx:
                            to_idx = url_to_idx[link]
                            adj_matrix[to_idx][from_idx] = 1.0 / outbound_count
        
        # Power iteration
        scores = np.ones(n) / n
        for _ in range(self.max_iterations):
            new_scores = (1 - self.damping_factor) / n + \
                        self.damping_factor * (adj_matrix @ scores)
            if np.sum(np.abs(new_scores - scores)) < self.threshold:
                break
            scores = new_scores
            
        # Store results
        self.scores = {url: float(score)*1000 for url, score 
                      in zip(urls, scores)}