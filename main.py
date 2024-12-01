import streamlit as st
import json
import time

from pathlib import Path
from indexer import Indexer

from search import SearchEngine, FileHandler
from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    INDEX_PEEK_FILE, 
    INDEX_MAP_FILE,
    DOCS_FILE,
    INDEX_FILE,
    DOC_TITLE_FILE
)

st.set_page_config(
    page_title='CS121 A3 Search Engine',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='auto'
)


@st.cache_data
def load_doc_titles():
    with open(DOC_TITLE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        return json.load(f)


@st.cache_resource
def initialize_search_engine():
    """Initialize and cache search engine instance"""
    return SearchEngine()


@st.cache_resource
def initialize_file_handler():
    """Initialize and cache file handler instance"""
    handler = FileHandler(INDEX_PEEK_FILE, INDEX_MAP_FILE)
    handler.__enter__()
    return handler


def display_search_results(results, query_time):
    """Display search results with clickable links"""
    st.write(f"Found {len(results)} results ({query_time:.3f} seconds)")
    for rank, result in enumerate(results, 1):
        with st.expander(f"**🔍 Result {rank} (Score: {result.score:.3f})**", expanded=True):
            title = st.session_state.doc_titles.get(result.url, result.url)
            st.markdown(f"##### [{title}]({result.url})")
            st.markdown(f"Matched terms: `{', '.join(result.matched_terms)}`")


def main():
    tab1, tab2 = st.tabs(["Search", "About"])

    with tab1:
        st.markdown("<h1 style='text-align: center;'>Search Engine</h1>", unsafe_allow_html=True)
        st.write("CS121 A3 Search Engine - by Jasper D & Max R")
        
        # Initialize cached components
        st.session_state.search_engine = initialize_search_engine()
        st.session_state.file_handler = initialize_file_handler()
        st.session_state.doc_titles = load_doc_titles()
        
        # Search interface
        col1, col2 = st.columns([5, 1])
        with col1:
            query = st.text_input("Enter your search query:")

        with col2:
            max_results = st.number_input("Max results", 5, 20, 10)
            
        if query:
            with st.spinner("Searching..."):
                start_time = time.time()
                
                results = st.session_state.search_engine.search(
                    query, 
                    max_results,
                    st.session_state.file_handler
                )
                
                query_time = time.time() - start_time
                display_search_results(results, query_time)
        else:
            st.info("Enter a search query to find relevant documents")

    with tab2:
        content = """
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
        """
        st.markdown(content)

if __name__ == "__main__":
    main()