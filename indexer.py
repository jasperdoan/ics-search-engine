import json
import math

from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Set

from utils.tokenizer import tokenize
from utils.constants import DATA_DIR


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

class Indexer:
    
    def __init__(self, data_dir: str = "./TEST"):
        self.data_dir = Path(data_dir)
        self.next_doc_id = 0
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.documents: Dict[int, str] = {}  # doc_id -> url
        self.processed_hashes: Set[int] = set()


    def extract_important_text(self, soup: BeautifulSoup) -> str:
        """Extract text from important HTML tags"""
        important_tags = soup.find_all(['b', 'strong', 'h1', 'h2', 'h3', 'title'])
        return ' '.join(tag.get_text() for tag in important_tags)


    def process_document(self, file_path: Path) -> None:
        """Process a single document and update the index"""
        try:
            # Load and parse document
            with open(file_path) as f:
                data = json.load(f)
            
            doc = Document(
                url=data['url'],
                content=data['content'],
                doc_id=self.next_doc_id
            )
            
            # Parse HTML
            soup = BeautifulSoup(doc.content, 'html.parser')
            text = soup.get_text()
            important_text = self.extract_important_text(soup)
            
            # Build frequency map
            freq_map: Dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
            
            # Process regular text
            for token in tokenize(text):
                count, imp = freq_map[token]
                freq_map[token] = (count + 1, imp)
                
            # Process important text
            for token in tokenize(important_text):
                count, imp = freq_map[token]
                freq_map[token] = (count * 2 if count > 0 else 1, imp + 1)
            
            # Check for duplicate content
            content_hash = hash(frozenset(freq_map.items()))
            if content_hash in self.processed_hashes:
                return
            
            # Update index
            for token, (freq, importance) in freq_map.items():
                tf_score = 1 + math.log10(freq) if freq > 0 else 0
                posting = Posting(doc.doc_id, freq, importance, tf_score)
                self.index[token].append(posting)
            
            self.documents[doc.doc_id] = doc.url
            self.processed_hashes.add(content_hash)
            self.next_doc_id += 1
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")


    def calculate_tf_idf(self) -> None:
        """Calculate TF-IDF scores for all terms"""
        num_docs = len(self.documents)
        for token, postings in self.index.items():
            idf = math.log10(num_docs / len(postings))
            for posting in postings:
                posting.tf_idf = posting.tf_idf * idf


    def build_index(self) -> None:
        """Build the complete index from documents"""
        for folder in self.data_dir.iterdir():
            if folder.is_dir():
                for file in folder.glob("*.json"):
                    self.process_document(file)
        self.calculate_tf_idf()


    def save_index(self, output_file: str = "index.json") -> None:
        """Save index to disk"""
        output = {
            "documents": self.documents,
            "index": {
                token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                       for p in postings]
                for token, postings in self.index.items()
            }
        }
        with open(output_file, 'w') as f:
            json.dump(output, f)


def main():
    indexer = Indexer()
    indexer.build_index()
    indexer.save_index()
    
    print(f"Documents indexed: {len(indexer.documents)}")
    print(f"Unique terms: {len(indexer.index)}")

if __name__ == "__main__":
    main()