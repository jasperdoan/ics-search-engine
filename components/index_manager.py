import json
import math
import sys

from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

from components.document_processor import Document
from utils.constants import (
    MAX_INDEX_SIZE_BYTES, 
    RANGE_SPLITS,
    PARTIAL_DIR,
    RANGE_DIR
    )

@dataclass
class Posting:
    doc_id: int
    frequency: int 
    importance: int
    tf_idf: float = 0.0

class IndexManager:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.partial_dir = Path(PARTIAL_DIR)
        self.range_dir = Path(RANGE_DIR)
        self.partial_dir.mkdir(exist_ok=True)
        self.range_dir.mkdir(exist_ok=True)
        self.partial_index_count = 0
        self.index_size = sys.getsizeof(self.index)

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
                print(f"\tCurrent index size (MB): {self.index_size / 1024 / 1024:.2f}")
                self.write_partial_index()
        return unique_terms

    def update_index_size(self, token: str, posting: Posting, adding: bool = True):
        """Update running index size when adding/removing items"""
        size_delta = (
            sys.getsizeof(token) +
            sys.getsizeof(posting)
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
        """Merge all partial indexes into 1 single final index"""
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

    def sort_partial_indexes_by_terms(self) -> None:
        """Merge partial indexes and split into range-based files"""
        range_indexes = defaultdict(lambda: defaultdict(list))
        
        # During merging all partials, sort by term range
        for i in range(self.partial_index_count):
            partial_path = self.partial_dir / f"partial_{i}.json"
            with open(partial_path, 'r') as f:
                partial_data = json.load(f)
                
            for token, postings in partial_data.items():
                term_range = self.get_term_range(token)
                for doc_id, freq, imp, tf_idf in postings:
                    posting = Posting(doc_id, freq, imp, tf_idf)
                    range_indexes[term_range][token].append(posting)

        # Save each range to separate file for searching later
        for term_range, terms in range_indexes.items():
            range_path = self.range_dir / f"index_{term_range}.json"
            
            index_output = {
                token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                    for p in postings]
                for token, postings in terms.items()
            }
            
            with open(range_path, 'w') as f:
                json.dump(index_output, f)
        
        print(f"\n========================================")
        print("\nIndex ranges created:")
        for path in self.range_dir.glob("*.json"):
            size_kb = path.stat().st_size / 1024
            print(f"- {path.name}: {size_kb:.2f} KB")

    def calculate_tf_idf(self, documents: Dict[int, Document]) -> None:
        """Calculate TF-IDF scores for all terms using stored token counts"""
        num_docs = len(documents)
        
        for _, postings in self.index.items():
            # IDF portion
            doc_freq = len(postings)  # number of docs containing this term
            idf = math.log10(num_docs / doc_freq)
            
            # Calculate TF-IDF for each term
            for posting in postings:
                # TF = frequency of term / total tokens in document
                tf = posting.frequency / documents[posting.doc_id].token_count
                weighted_tf = tf * (1 + posting.importance)
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
            
    def get_term_range(self, term: str) -> str:
        """Determine which range a term belongs to"""
        if not term:
            return "misc"
        
        first_char = term[0].lower()
        if not first_char.isalpha():
            return "misc"
            
        for start, end in RANGE_SPLITS:
            if start <= first_char <= end:
                return f"{start}_{end}"
        return "misc"
