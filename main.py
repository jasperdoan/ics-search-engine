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
    st.title("Search Engine")
    st.write("CS121 A3 Search Engine - by Jasper D, & Max R")
    
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

if __name__ == "__main__":
    main()