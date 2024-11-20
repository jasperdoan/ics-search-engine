import json
import math
import sys

from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

from components.document_processor import Document
from utils.constants import (
    CONFIG,
    PARTIAL_DIR,
    RANGE_DIR
    )

@dataclass
class Posting:
    doc_id: int
    frequency: int 
    importance: int
    tf_idf: float
    positions: List[int]


class IndexManager:
    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.partial_dir = Path(PARTIAL_DIR)
        self.range_dir = Path(RANGE_DIR)
        self.partial_dir.mkdir(exist_ok=True)
        self.range_dir.mkdir(exist_ok=True)
        self.partial_index_count = 0
        self.index_size = sys.getsizeof(self.index)

    def _calculate_tf_idf_for_postings(self, postings: List[Posting], documents: Dict[int, Document], num_docs: int) -> List[Posting]:
        """Generic function to calculate TF-IDF scores for a list of postings"""
        # IDF calculation
        doc_freq = len(postings)
        idf = math.log10(num_docs / doc_freq)
        
        # Calculate TF-IDF for each posting
        for posting in postings:
            try:
                tf = posting.frequency / documents[posting.doc_id].token_count
            except ZeroDivisionError:
                tf = 0
            weighted_tf = tf * (1 + posting.importance)
            posting.tf_idf = weighted_tf * idf
        return postings

    def update_index(self, freq_map, doc_id):
        """Update index with new document's tokens"""
        unique_terms = 0
        for token, (freq, importance, positions) in freq_map.items():
            posting = Posting(doc_id, freq, importance, 0.0, positions)
            self.index[token].append(posting)
            self.update_index_size(token, posting)
            unique_terms += 1
            
            if self.index_size > CONFIG['max_index_size']:
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
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf, p.positions)
                for p in postings]
            for token, postings in self.index.items()
        }
        
        with open(partial_path, 'w') as f:
            json.dump(index_output, f)
            
        self.partial_index_count += 1
        self.index.clear()
        self.index_size = sys.getsizeof(self.index)

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
                for doc_id, freq, imp, tf_idf, pos in postings:
                    posting = Posting(doc_id, freq, imp, tf_idf, pos)
                    range_indexes[term_range][token].append(posting)

        # Save each range to separate file for searching later
        for term_range, terms in range_indexes.items():
            range_path = self.range_dir / f"index_{term_range}.json"
            
            index_output = {
                token: [(p.doc_id, p.frequency, p.importance, p.tf_idf, p.positions)
                    for p in postings]
                for token, postings in terms.items()
            }
            with open(range_path, 'w') as f:
                json.dump(index_output, f)

    def calculate_range_tf_idf(self, documents: Dict[int, Document]) -> None:
        """Calculate TF-IDF scores for range indexes"""
        num_docs = len(documents)
        print(f"\n========================================")
        print("Calculating TF-IDF scores for range indexes...")
        
        for range_path in self.range_dir.glob("*.json"):
            print(f"\nProcessing range file: {range_path.name}")
            
            with open(range_path, 'r') as f:
                range_data = json.load(f)
                
            updated_range = {}
            for token, postings in range_data.items():
                # Convert raw postings to Posting objects
                posting_objects = [
                    Posting(doc_id, freq, imp, 0.0, pos)
                    for doc_id, freq, imp, _, pos in postings
                ]
                
                # Calculate TF-IDF using shared function
                updated_postings = self._calculate_tf_idf_for_postings(posting_objects, documents, num_docs)
                
                # Convert back to serializable format
                updated_range[token] = [
                    (p.doc_id, p.frequency, p.importance, p.tf_idf, p.positions)
                    for p in updated_postings
                ]
            
            with open(range_path, 'w') as f:
                json.dump(updated_range, f)
            
            size_kb = range_path.stat().st_size / 1024
            print(f"Updated {range_path.name}: {size_kb:.2f} KB")

    def merge_indexes(self) -> None:
        """Merge all range index files into a single final index"""
        merged_index = defaultdict(list)
        range_files = list(self.range_dir.glob("index_*.json"))
        print(f"\n========================================")
        print(f"Merging {len(range_files)} range indexes...")
        print(f"========================================")
        for range_path in range_files:
            try:
                with open(range_path, 'r') as f:
                    range_data = json.load(f)
                for token, postings in range_data.items():
                    for doc_id, freq, imp, tf_idf, pos in postings:
                        posting = Posting(doc_id, freq, imp, tf_idf, pos)
                        merged_index[token].append(posting)
            except Exception as e:
                print(f"Error processing {range_path}: {e}")
        self.index = merged_index

    def save_index(self, path: str) -> None:
        """Save index to file with positions"""
        index_output = {
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf, p.positions)
                for p in postings]
            for token, postings in self.index.items()
        }
        
        with open(path, 'w') as f:
            json.dump(index_output, f)
            
    def get_term_range(self, term: str) -> str:
        """Determine which range a term belongs to"""
        if not term:
            return "misc"
        return f"{term[0].lower()}"