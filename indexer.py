import json

from pathlib import Path
from typing import Dict, List, Callable, Optional
from bs4 import BeautifulSoup
from tqdm import tqdm

from components.document_processor import DocumentProcessor, Document
from components.token_processor import TokenProcessor
from components.index_manager import IndexManager
from utils.hits import HITS
from utils.pagerank import PageRank
from utils.index_generator import IndexGenerator
from utils.partials_handler import convert_json_to_pickle
from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    DOCS_FILE,
    INDEX_FILE,
    FULL_ANALYTICS_DIR,
    CONFIG,
    INDEX_PEEK_FILE, 
    INDEX_MAP_FILE
)

class Indexer:
    def __init__(self, data_dir: str = DEV_DIR):
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
            # print(f"\nProcessing {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data['url'].lower().endswith('.txt'):
                # print(f"\tSkipping .txt file: {data['url']}")
                return

            # Process document content
            soup, text = self.doc_processor.soupify(data)
            weighted_text = self.doc_processor.extract_important_text(soup)
            doc = self.doc_processor.create_document(data, text, self.next_doc_id)

            # Extract links for HITS
            links = self.doc_processor.extract_links(BeautifulSoup(data.get('content', ''), 'html.parser'), data['url'])
            doc.outgoing_links = links
            
            # Check for near-duplicates
            if self.doc_processor.is_near_duplicate(doc.simhash, self.documents, CONFIG['similarity_threshold']):
                return
            
            # Process tokens with weighted important text
            freq_map = self.token_processor.process_tokens(text, weighted_text)
            unique_terms = self.index_manager.update_index(freq_map, doc.doc_id)
            
            # print(f"\tAdded {unique_terms} unique terms to index")
            
            self.documents[doc.doc_id] = doc
            self.next_doc_id += 1
            
        except Exception as e:
            print(f"\tError processing {file_path}: {e}")

    def set_progress_callback(self, callback: Callable) -> None:
        self.progress_callback = callback

    def build_index(self) -> None:
        """Build the complete index from documents"""
        self.files_processed = 0
        
        # Get all json files first
        all_files = []
        for folder in self.data_dir.iterdir():
            if folder.is_dir():
                all_files.extend(folder.glob("*.json"))
                
        # Create progress bar
        with tqdm(total=len(all_files), desc="Indexing documents") as pbar:
            for file in all_files:
                self.process_document(file)
                self.files_processed += 1
                if self.progress_callback:
                    progress = (self.files_processed / self.total_files) * 100
                    self.progress_callback(progress)
                pbar.update(1)
        
        # Final write if there's still data in index
        if self.index_manager.index:
            self.index_manager.write_partial_index()
            
        # Add progress bars for post-processing
        print("\nPost-processing indexes...")
        
        with tqdm(desc="Sorting indexes by terms") as pbar:
            self.index_manager.sort_partial_indexes_by_terms()
            pbar.update(1)
            
        with tqdm(desc="Calculating TF-IDF scores") as pbar:
            self.index_manager.calculate_range_tf_idf(self.documents)
            pbar.update(1)

    def save_data(self) -> None:
        """Save documents and index to files"""
        documents_output = {
            doc_id: {
                "url": doc.url,
                "simhash": doc.simhash,
                "token_count": doc.token_count,
                "outgoing_links": doc.outgoing_links
            } for doc_id, doc in self.documents.items()
        }
        
        with open(DOCS_FILE, 'w') as f:
            json.dump(documents_output, f)

        # Compute and save HITS + PageRank scores
        print("\nComputing HITS + PageRank scores...")
        hits = HITS()
        pagerank = PageRank()

        hits.compute_scores(documents_output)    
        pagerank.compute_scores(documents_output)

        scores = {
            'hits': {
                'authority': hits.auth_scores,
                'hub': hits.hub_scores
            },
            'pagerank': pagerank.scores
        }
            
        with open(Path(FULL_ANALYTICS_DIR) / 'link_scores.json', 'w') as f:
            json.dump(scores, f)

        self.index_manager.merge_indexes()
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
    generator = IndexGenerator(
        index_path=INDEX_FILE,
        output_pickle=INDEX_PEEK_FILE,
        output_json=INDEX_MAP_FILE
    )
    generator.generate()

if __name__ == "__main__":
    main()