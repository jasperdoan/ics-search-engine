import json
import math

from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from multiprocessing import Pool, Manager, cpu_count
from functools import partial

from utils.tokenizer import tokenize
from utils.simhash import SimHash
from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    SIMILARITY_THRESHOLD,
    NEAR_DUPLICATE_LENGTH_DIFF,
    DOCS_FILE,
    INDEX_FILE,
    IMPORTANT_HTML_TAGS
)



@dataclass
class Posting:
    doc_id: int
    frequency: int 
    importance: int
    tf_idf: float = 0.0


@dataclass
class Document:
    url: str
    content: str
    doc_id: int
    simhash: str = ""


class Indexer:
    def __init__(self, data_dir: str = TEST_DIR):
        self.data_dir = Path(data_dir)
        self.next_doc_id = 0
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.documents: Dict[int, Document] = {}
        self.simhasher = SimHash()
        self.total_files = sum(1 for _ in Path(data_dir).rglob("*.json"))
        self.files_processed = 0
        self.progress_callback = None


    def extract_important_text(self, soup: BeautifulSoup) -> str:
        """Extract text from important HTML tags"""
        important_tags = soup.find_all(IMPORTANT_HTML_TAGS)
        return ' '.join(tag.get_text() for tag in important_tags)


    def is_near_duplicate(self, content: str, simhash: str) -> bool:
        """Check if document is a near-duplicate of existing documents"""
        for existing_doc in self.documents.values():
            if abs(len(content) - len(existing_doc.content)) < NEAR_DUPLICATE_LENGTH_DIFF:
                similarity_score = 1 - self.simhasher.hamming_distance(simhash, existing_doc.simhash) / self.simhasher.b
                if similarity_score >= SIMILARITY_THRESHOLD:
                    print(f"\tNear-duplicate document detected to {existing_doc.doc_id}, being {100*similarity_score:.2f}% similar")
                    return True
        return False


    def create_document(self, data: dict) -> Document:
        """Create a new Document instance from JSON data"""
        simhash = self.simhasher.compute_simhash(data['content'])
        return Document(
            url=data['url'],
            content=data['content'],
            doc_id=self.next_doc_id,
            simhash=simhash
        )


    def process_tokens(self, text: str, important_text: str) -> Dict[str, Tuple[int, int]]:
        """Process regular and important tokens to create frequency map"""
        freq_map = defaultdict(lambda: (0, 0))
        
        # Process regular text
        regular_tokens = tokenize(text)
        print(f"\tRegular tokens: {len(regular_tokens)}")
        
        for token in regular_tokens:
            count, imp = freq_map[token]
            freq_map[token] = (count + 1, imp)
            
        # Process important text
        important_tokens = tokenize(important_text)
        print(f"\tImportant tokens: {len(important_tokens)}")
        
        for token in important_tokens:
            count, imp = freq_map[token]
            freq_map[token] = (count * 2 if count > 0 else 1, imp + 1)
            
        return freq_map


    def update_index(self, freq_map: Dict[str, Tuple[int, int]], doc_id: int) -> int:
        """Update index with new document's tokens"""
        unique_terms = 0
        for token, (freq, importance) in freq_map.items():
            tf_score = 1 + math.log10(freq) if freq > 0 else 0
            posting = Posting(doc_id, freq, importance, tf_score)
            self.index[token].append(posting)
            unique_terms += 1
        return unique_terms


    def process_document(self, file_path: Path) -> None:
        """Process a single document and update the index"""
        try:
            print(f"\nProcessing {file_path}")
            
            with open(file_path) as f:
                data = json.load(f)
            
            # Create document and check for duplicates
            doc = self.create_document(data)
            if self.is_near_duplicate(doc.content, doc.simhash):
                return
            
            # Extract text content
            soup = BeautifulSoup(doc.content, 'html.parser')
            text = soup.get_text()
            important_text = self.extract_important_text(soup)
            
            # Process tokens and update index
            freq_map = self.process_tokens(text, important_text)
            unique_terms = self.update_index(freq_map, doc.doc_id)
            
            print(f"\tAdded {unique_terms} unique terms to index")
            
            self.documents[doc.doc_id] = doc
            self.next_doc_id += 1
            
        except Exception as e:
            print(f"\tError processing {file_path}: {e}")


    def calculate_tf_idf(self) -> None:
        """Calculate TF-IDF scores for all terms"""
        num_docs = len(self.documents)
        for token, postings in self.index.items():
            idf = math.log10(num_docs / len(postings))
            for posting in postings:
                posting.tf_idf = posting.tf_idf * idf


    def set_progress_callback(self, callback):
        self.progress_callback = callback


    def build_index(self) -> None:
        """Build the complete index from documents"""
        self.files_processed = 0
        for folder in self.data_dir.iterdir():
            if folder.is_dir():
                for file in folder.glob("*.json"):
                    self.process_document(file)
                    self.files_processed += 1
                    if self.progress_callback:
                        progress = (self.files_processed / self.total_files) * 100
                        self.progress_callback(progress)
        self.calculate_tf_idf()


    def save_index(self) -> None:
        """Save documents and index to separate files and report their sizes"""
        # Prepare documents output
        documents_output = {
            doc_id: {
                "url": doc.url,
                "simhash": doc.simhash,
                "length": len(doc.content)
            } for doc_id, doc in self.documents.items()
        }
        
        # Prepare index output
        index_output = {
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                for p in postings]
            for token, postings in self.index.items()
        }
        
        # Save documents
        with open(DOCS_FILE, 'w') as f:
            json.dump(documents_output, f)
            
        # Save index
        with open(INDEX_FILE, 'w') as f:
            json.dump(index_output, f)
        
        # Calculate file sizes
        docs_size_kb = Path(DOCS_FILE).stat().st_size / 1024
        index_size_kb = Path(INDEX_FILE).stat().st_size / 1024
        
        print(f"\n========================================")
        print(f"Documents indexed:  {len(self.documents)}")
        print(f"Unique tokens:      {len(self.index)}")
        print(f"Index file size:    {index_size_kb:.2f} KB")
        print(f"========================================\n")
        print(f"Documents saved to {DOCS_FILE}")
        print(f"Index saved to {INDEX_FILE}")



def main():
    indexer = Indexer()
    indexer.build_index()
    indexer.save_index()

if __name__ == "__main__":
    main()