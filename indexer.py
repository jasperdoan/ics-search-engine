import json

from pathlib import Path
from typing import Dict, List, Callable, Optional

from components.document_processor import DocumentProcessor, Document
from components.token_processor import TokenProcessor
from components.index_manager import IndexManager
from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    DOCS_FILE,
    INDEX_FILE,
    FULL_ANALYTICS_DIR,
    SIMILARITY_THRESHOLD
)

class Indexer:
    def __init__(self, data_dir: str = ANALYST_DIR):
        self.data_dir = Path(data_dir)
        self.stats_dir = Path(FULL_ANALYTICS_DIR)
        self.stats_dir.mkdir(exist_ok=True)
        self.next_doc_id = 0
        self.documents: Dict[int, Document] = {}
        
        # Components
        self.doc_processor = DocumentProcessor()
        self.token_processor = TokenProcessor()
        self.index_manager = IndexManager()
        
        # Progress tracking
        self.total_files = sum(1 for _ in Path(data_dir).rglob("*.json"))
        self.files_processed = 0
        self.progress_callback: Optional[Callable] = None

    def process_document(self, file_path: Path) -> None:
        """Process a single document and update the index"""
        try:
            print(f"\nProcessing {file_path}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Process document content
            soup, text = self.doc_processor.soupify(data)
            weighted_text = self.doc_processor.extract_important_text(soup)
            doc = self.doc_processor.create_document(data, text, self.next_doc_id)

            # Check for near-duplicates
            if self.doc_processor.is_near_duplicate(doc.simhash, self.documents, SIMILARITY_THRESHOLD):
                return
            
            # Process tokens with weighted important text
            freq_map = self.token_processor.process_tokens(text, weighted_text)
            unique_terms = self.index_manager.update_index(freq_map, doc.doc_id)
            
            print(f"\tAdded {unique_terms} unique terms to index")
            
            self.documents[doc.doc_id] = doc
            self.next_doc_id += 1
            
        except Exception as e:
            print(f"\tError processing {file_path}: {e}")

    def set_progress_callback(self, callback: Callable) -> None:
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
        
        if self.index_manager.index:
            self.index_manager.write_partial_index()
        self.index_manager.merge_partial_indexes()
        self.index_manager.sort_partial_indexes_by_terms()
        self.index_manager.calculate_tf_idf(len(self.documents))

    def save_data(self) -> None:
        """Save documents and index to files"""
        documents_output = {
            doc_id: {
                "url": doc.url,
                "simhash": doc.simhash,
            } for doc_id, doc in self.documents.items()
        }
        
        with open(DOCS_FILE, 'w') as f:
            json.dump(documents_output, f)
            
        self.index_manager.save_index(INDEX_FILE)
        
        # Print statistics
        docs_size_kb = Path(DOCS_FILE).stat().st_size / 1024
        index_size_kb = Path(INDEX_FILE).stat().st_size / 1024
        
        print(f"\n========================================")
        print(f"Documents indexed:  {len(self.documents)}")
        print(f"Unique tokens:      {len(self.index_manager.index)}")
        print(f"Index file size:    {index_size_kb:.2f} KB")
        print(f"========================================\n")
        print(f"Documents saved to {DOCS_FILE}")
        print(f"Index saved to {INDEX_FILE}")

def main():
    indexer = Indexer()
    indexer.build_index()
    indexer.save_data()

if __name__ == "__main__":
    main()