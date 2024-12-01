# Search Engine Overview

Our search engine provides fast and accurate search capabilities across UCI's ICS domain. It combines modern information retrieval techniques with efficient data structures to deliver results in milliseconds.

## Performance Metrics
| Query Type | Response Time |
|------------|---------------|
| Single term | 10-100ms |
| Multi-term | 100-200ms |
| Complex (5+ terms) | 200-300ms |

## Core Architecture

The system is built on four main components working in harmony:

1. **Document Processing Pipeline**

| Component | Function |
|-----------|-----------|
| HTML Parser | Extracts clean text from web pages using BeautifulSoup4 |
| Text Analyzer | Identifies important content from headers and titles |
| Duplicate Detector | Prevents index bloat using SimHash algorithm |

2. **Search Algorithm**

| Feature | Description |
|---------|-------------|
| TF-IDF Scoring | Measures term importance in documents |
| Cosine Similarity | Computes relevance between query and documents |
| PageRank & HITS | Incorporates web graph authority signals |

3. **Index Management**

| Strategy | Implementation |
|----------|----------------|
| Storage | Hybrid Pickle/JSON for optimal speed/space tradeoff |
| Access | Peek-based retrieval to minimize memory usage |
| Caching | LRU cache for frequent terms and queries |

4. **Query Processing**

| Stage | Operation |
|-------|-----------|
| Tokenization | NLTK-based text normalization |
| Stemming | Porter stemming for word variations |
| Ranking | Multi-factor score combining relevance signals |

## Technical Implementation 

The codebase is organized into focused modules:

- [`search.py`](src/search.py): Core search logic and ranking
- [`indexer.py`](src/indexer.py): Document processing and index building 
- [`token_processor.py`](src/components/token_processor.py): Text analysis and normalization
- [`document_processor.py`](src/components/document_processor.py): HTML handling and deduplication


## Data Structures

### Document
```python
@dataclass
class Document:
    url: str                    # Document URL
    content: str                # Processed raw text content
    doc_id: int                 # Unique document identifier
    simhash: str                # SimHash fingerprint for deduplication
    token_count: int            # Number of tokens in document
    outgoing_links: List[str]   # Outgoing URLs for link analysis
```

### Posting
```python
@dataclass
class Posting:
    doc_id: int            # Document identifier
    frequency: int         # Term frequency in document
    importance: float      # Combined weight from HTML tags
    tf_idf: float          # Term frequency-inverse document frequency score
    positions: List[int]   # Token positions for phrase queries
```

### Index Structure
```python
{
    "term1": [Posting1, Posting2, ...],
    "term2": [Posting3, Posting4, ...],
    ...
}
```

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