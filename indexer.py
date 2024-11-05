import json
import math

from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Set

from utils.tokenizer import tokenize
from utils.simhash import SimHash
from utils.constants import DATA_DIR, SIMILARITY_THRESHOLD


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
    def __init__(self, data_dir: str = "./TEST"):
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
        important_tags = soup.find_all(['b', 'strong', 'h1', 'h2', 'h3', 'title'])
        return ' '.join(tag.get_text() for tag in important_tags)


    def process_document(self, file_path: Path) -> None:
        """Process a single document and update the index"""
        try:
            print(f"\nProcessing {file_path}")
            
            with open(file_path) as f:
                data = json.load(f)
            
            # Calculate SimHash first
            simhash = self.simhasher.compute_simhash(data['content'])
            
            # Check for near-duplicates
            for existing_doc in self.documents.values():
                if abs(len(data['content']) - len(existing_doc.content)) < 1000:  # Only compare similar lengths
                    if 1 - self.simhasher.hamming_distance(simhash, existing_doc.simhash) / self.simhasher.b >= SIMILARITY_THRESHOLD:
                        print(f"\tNear-duplicate document detected to {existing_doc.doc_id}, skipping")
                        return
            
            doc = Document(
                url=data['url'],
                content=data['content'],
                doc_id=self.next_doc_id,
                simhash=simhash
            )
            
            soup = BeautifulSoup(doc.content, 'html.parser')
            text = soup.get_text()
            important_text = self.extract_important_text(soup)
            
            print(f"\tFound {len(important_text.split())} words in important sections")
            
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
                
            # Update index
            unique_terms = 0
            for token, (freq, importance) in freq_map.items():
                tf_score = 1 + math.log10(freq) if freq > 0 else 0
                posting = Posting(doc.doc_id, freq, importance, tf_score)
                self.index[token].append(posting)
                unique_terms += 1
            
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


    def save_index(self, output_file: str = "index.json") -> None:
        """Save index to disk and report its size"""
        total_postings = sum(len(postings) for postings in self.index.values())
        output = {
            "documents": {
                doc_id: {
                    "url": doc.url,
                    "simhash": doc.simhash,
                    "length": len(doc.content)
                } for doc_id, doc in self.documents.items()
            },
            "index": {
                token: [(p.doc_id, p.frequency, p.importance, p.tf_idf) 
                    for p in postings]
                for token, postings in self.index.items()
            }
        }
        with open(output_file, 'w') as f:
            json.dump(output, f)
            
        # Get file size
        file_size_bytes = Path(output_file).stat().st_size
        file_size_kb = file_size_bytes / 1024

        print("\n==================================")
        print(f"Total documents indexed: {len(self.documents)}")
        print(f"Total unique tokens: {len(self.index)}")
        print(f"Index size: {file_size_kb:.2f} KB")
        print("==================================\n")
        print(f"Index saved to {output_file}")



def main():
    indexer = Indexer()
    indexer.build_index()
    indexer.save_index()

if __name__ == "__main__":
    main()