# CS121 Search Engine

A high-performance search engine built for CS121 that indexes and searches UCI ICS website content.

## Features

- Fast search with average query times of 0.01s-0.2s
- Advanced ranking using:
  - TF-IDF scoring
  - Cosine similarity
  - Term match boosting
- Near-duplicate detection using SimHash
- Smart caching system for frequently accessed terms
- Efficient index storage and retrieval using hybrid Pickle/JSON approach

## Architecture

### Core Components

- **Indexer**: Builds the search index from documents
- **Search Engine**: Handles query processing and result ranking
- **Document Processor**: Processes HTML content and detects duplicates
- **Token Processor**: Handles text tokenization and normalization
- **Index Manager**: Manages index storage and retrieval

### Search Algorithm
- Multi-factor ranking combining:
  - TF-IDF: Term frequency-inverse document frequency scoring
  - Cosine Similarity: Vector space model comparison
  - Term Match Boost: Rewards matching more query terms
  - Important Text Weighting: HTML tags like titles and headers get higher weights
- Query optimization using peek-based index access
- Cache system for frequent queries

### Index Structure
1. **Document Processing**
   - HTML parsing with BeautifulSoup4
   - Text extraction and cleaning
   - Important text weighting based on HTML tags
   - SimHash-based near-duplicate detection

2. **Token Processing**
   - NLTK-based tokenization
   - Porter stemming
   - Stop word removal
   - Position tracking for each term

3. **Index Storage**
   - Hybrid storage using Pickle and JSON
   - Index sharding for efficient access
   - Seek-based partial loading
   - Optimized for memory efficiency

### Key Files

- `main.py`: Web interface using Streamlit
- `indexer.py`: Core indexing logic
- `search.py`: Search implementation
- `document_processor.py`: Document processing and deduplication
- `token_processor.py`: Text tokenization and processing

## Performance Optimizations

1. **Hybrid Storage Strategy**
   - Uses Pickle for fast binary storage
   - JSON map file for efficient term location lookup
   - Peek-based retrieval for minimal memory usage

2. **Smart Caching**
   - Caches frequent/recent search results
   - Configurable cache size limits
   - Balanced memory usage vs performance

3. **Duplicate Detection**
   - SimHash-based near-duplicate detection
   - Configurable similarity threshold
   - Improves result quality and index size

## Usage

1. Build the index:
```python
python3 indexer.py
```

2. Start the search engine:
```python
# For UI
streamlit run main.py

# For CLI
python3 search.py
```

## Requirements
- Python 3.7+
- Streamlit
- NLTK
- BeautifulSoup4
- NumPy
- SciPy
- scikit-learn

## Performance
Typical query performance:
- Single term queries: 0.01s - 0.1s
- Multi-term queries: 0.1s - 0.2s
- Complex queries (5+ terms): 0.2s - 0.3s