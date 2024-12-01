import sys
import json
import queue
import random
import threading

from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import defaultdict

from indexer import Indexer
from components.document_processor import DocumentProcessor, Document
from components.token_processor import TokenProcessor
from components.index_manager import IndexManager, Posting
from utils.hits import HITS
from utils.pagerank import PageRank
from utils.index_generator import IndexGenerator
from utils.partials_handler import convert_json_to_pickle
from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    PARTIAL_DIR,
    DOCS_FILE,
    INDEX_FILE,
    FULL_ANALYTICS_DIR,
    CONFIG,
    INDEX_PEEK_FILE, 
    INDEX_MAP_FILE
)



class IndexWorker:
    def __init__(self, worker_id: int, files: List[Path], shared_resources, master_pbar):
        self.worker_id = worker_id
        self.files = files
        self.doc_processor = DocumentProcessor()
        self.token_processor = TokenProcessor()
        self.local_index = defaultdict(list)
        self.shared = shared_resources
        self.master_pbar = master_pbar
        self.worker_pbar = tqdm(
            total=len(files),
            desc=f"Worker {worker_id}",
            position=worker_id + 1,
            leave=True
        )
        self.local_index_size = 0
        self.partial_count = 0

    def write_partial_index(self):
        """Write current local index to disk"""
        if not self.local_index:
            return
            
        partial_path = Path(PARTIAL_DIR) / f"partial_w{self.worker_id}_{self.partial_count}.json"
        Path(PARTIAL_DIR).mkdir(exist_ok=True)
        
        index_output = {
            token: [(p.doc_id, p.frequency, p.importance, p.tf_idf, p.positions)
                for p in postings]
            for token, postings in self.local_index.items()
        }
        
        with open(partial_path, 'w') as f:
            json.dump(index_output, f)
            
        self.partial_count += 1
        self.local_index.clear()
        self.local_index_size = 0

    def update_index_size(self, token: str, posting: Posting):
        """Track local index size"""
        size_delta = (
            sys.getsizeof(token) +
            sys.getsizeof(posting)
        )
        self.local_index_size += size_delta
        
        # Write partial if size exceeds threshold
        if self.local_index_size > CONFIG['max_index_size']:
            print(f"\nWorker {self.worker_id} writing partial index...")
            self.write_partial_index()
        
    def process_files(self):
        for file_path in self.files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if data['url'].lower().endswith('.txt'):
                    continue

                soup, text = self.doc_processor.soupify(data)
                weighted_text = self.doc_processor.extract_important_text(soup)
                
                with self.shared.doc_id_lock:
                    doc_id = self.shared.next_doc_id
                    self.shared.next_doc_id += 1
                
                doc = self.doc_processor.create_document(data, text, doc_id)
                links = self.doc_processor.extract_links(soup, data['url'])
                doc.outgoing_links = links

                with self.shared.doc_lock:
                    if not self.doc_processor.is_near_duplicate(
                        doc.simhash, self.shared.documents, CONFIG['similarity_threshold']):
                        freq_map = self.token_processor.process_tokens(text, weighted_text)
                        
                        for token, (freq, imp, positions) in freq_map.items():
                            posting = Posting(doc_id, freq, imp, 0.0, positions)
                            self.local_index[token].append(posting)
                            self.update_index_size(token, posting)
                        
                        self.shared.documents[doc_id] = doc
                
                self.master_pbar.update(1)
                self.worker_pbar.update(1)
                        
            except Exception as e:
                print(f"Worker {self.worker_id} error processing {file_path}: {e}")
                self.master_pbar.update(1)
                self.worker_pbar.update(1)
        
        # Write any remaining index data
        if self.local_index:
            self.write_partial_index()
            
        self.worker_pbar.close()



class SharedResources:
    def __init__(self):
        self.doc_lock = Lock()
        self.doc_id_lock = Lock()
        self.next_doc_id = 0
        self.documents = {}



class MultithreadedIndexer(Indexer):
    def __init__(self, data_dir: str = DEV_DIR, num_workers: int = 4):
        super().__init__(data_dir)
        self.num_workers = num_workers
        self.shared = SharedResources()
        
    def divide_work(self, all_files: List[Path]) -> List[List[Path]]:
        """Divide files equally among workers"""
        files_per_worker = len(all_files) // self.num_workers
        return [
            all_files[i:i + files_per_worker] 
            for i in range(0, len(all_files), files_per_worker)
        ]

    def build_index(self) -> None:
        print(f"\nStarting indexing with {self.num_workers} workers...")
        
        # Collect all files
        all_files = []
        for folder in self.data_dir.iterdir():
            if folder.is_dir():
                all_files.extend(folder.glob("*.json"))
        random.shuffle(all_files)
        random.shuffle(all_files)
        random.shuffle(all_files)
        random.shuffle(all_files)
        random.shuffle(all_files)

        # Initialize progress bars
        total_files = len(all_files)
        master_pbar = tqdm(
            total=total_files,
            desc="Total Progress",
            position=0,
            leave=True
        )

        # Create workers and threads
        work_divisions = self.divide_work(all_files)
        workers = []
        threads = []

        for i in range(self.num_workers):
            worker = IndexWorker(
                worker_id=i,
                files=work_divisions[i],
                shared_resources=self.shared,
                master_pbar=master_pbar
            )
            workers.append(worker)
            thread = threading.Thread(target=worker.process_files)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        master_pbar.close()

        # Post-processing progress
        print("\nMerging worker indexes...")
        with tqdm(total=len(workers), desc="Merging indexes") as merge_pbar:
            for worker in workers:
                for token, postings in worker.local_index.items():
                    self.index_manager.index[token].extend(postings)
                merge_pbar.update(1)
        
        # Copy shared documents
        self.documents = self.shared.documents
        
        print("\nPost-processing indexes...")
        with tqdm(desc="Sorting indexes by terms") as pbar:
            self.index_manager.sort_partial_indexes_by_terms()
            pbar.update(1)
            
        with tqdm(desc="Calculating TF-IDF scores") as pbar:
            self.index_manager.calculate_range_tf_idf(self.documents)
            pbar.update(1)


def main():
    indexer = MultithreadedIndexer(num_workers=16)
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