import json
import math
import sys

from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

from utils.constants import MAX_INDEX_SIZE_BYTES

@dataclass
class Posting:
    doc_id: int
    frequency: int 
    importance: int
    tf_idf: float = 0.0

class IndexManager:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.partial_dir = Path("partial_indexes")
        self.partial_dir.mkdir(exist_ok=True)
        self.partial_index_count = 0
        self.index_size = sys.getsizeof(self.index)

    def get_index_size(self) -> int:
        """Calculate approximate size of current index in bytes"""
        size = sys.getsizeof(self.index)
        for token, postings in self.index.items():
            size += sys.getsizeof(token)
            size += sys.getsizeof(postings)
            for posting in postings:
                size += sys.getsizeof(posting)
        return size

    def update_index(self, freq_map: Dict[str, Tuple[int, int]], doc_id: int) -> int:
        """Update index with new document's tokens"""
        unique_terms = 0
        for token, (freq, importance) in freq_map.items():
            tf_score = 1 + math.log10(freq) if freq > 0 else 0
            posting = Posting(doc_id, freq, importance, tf_score)
            self.index[token].append(posting)
            self.update_index_size(token, posting)  # Track size increase
            unique_terms += 1
            
            if self.index_size > MAX_INDEX_SIZE_BYTES:
                print(f"\tIndex size exceeded threshold, writing partial index to disk")
                self.write_partial_index()
        return unique_terms

    def update_index_size(self, token: str, posting: Posting, adding: bool = True):
        """Update running index size when adding/removing items"""
        size_delta = (
            sys.getsizeof(token) +
            sys.getsizeof(posting) +
            sys.getsizeof(self.index[token])
        )
        self.index_size += size_delta if adding else -size_delta

    def write_partial_index(self) -> None:
        """Write current index to disk as a partial index"""
        if not self.index:
            return
            
        partial_path = self.partial_dir / f"partial_{self.partial_index_count}.json"
        
        index_output = {
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                for p in postings]
            for token, postings in self.index.items()
        }
        
        with open(partial_path, 'w') as f:
            json.dump(index_output, f)
            
        self.partial_index_count += 1
        self.index.clear()
        self.index_size = sys.getsizeof(self.index)

    def merge_partial_indexes(self) -> None:
        """Merge all partial indexes into final index"""
        merged_index = defaultdict(list)
        
        for i in range(self.partial_index_count):
            partial_path = self.partial_dir / f"partial_{i}.json"
            with open(partial_path, 'r') as f:
                partial_data = json.load(f)
                
            for token, postings in partial_data.items():
                for doc_id, freq, imp, tf_idf in postings:
                    posting = Posting(doc_id, freq, imp, tf_idf)
                    merged_index[token].append(posting)

        self.index = merged_index

    def add_posting(self, token: str, doc_id: int, freq: int, importance: int) -> None:
        """Add a new posting to the index"""
        tf_score = 1 + math.log10(freq) if freq > 0 else 0
        posting = Posting(doc_id, freq, importance, tf_score)
        self.index[token].append(posting)
        self.update_index_size(token, posting)

    def calculate_tf_idf(self, num_docs: int) -> None:
        """Calculate TF-IDF scores for all terms"""
        # TF portion
        doc_lengths = defaultdict(int)
        for _, postings in self.index.items():
            for posting in postings:
                doc_lengths[posting.doc_id] += posting.frequency

        for token, postings in self.index.items():
            # IDF portion
            doc_freq = len(postings)  # number of docs containing this term
            idf = math.log10(num_docs / doc_freq)
            
            # Calculate TF-IDF for each term
            for posting in postings:
                # TF = frequency of term / total terms in document
                tf = posting.frequency / doc_lengths[posting.doc_id]
                weighted_tf = tf * (1 + posting.importance)  

                # TF-IDF score
                posting.tf_idf = weighted_tf * idf

    def save_index(self, path: str) -> None:
        """Save index to file"""
        index_output = {
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                for p in postings]
            for token, postings in self.index.items()
        }
        
        with open(path, 'w') as f:
            json.dump(index_output, f)