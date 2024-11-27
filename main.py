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
    INDEX_FILE
)

st.set_page_config(
    page_title='CS121 A3 Search Engine',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='auto'
)


def load_json_data():
    """Load JSON data into session state if not already loaded"""
    if 'index_data' not in st.session_state or 'docs_data' not in st.session_state:
        try:
            with open(INDEX_FILE, "r") as f:
                st.session_state.index_data = json.load(f)
            with open(DOCS_FILE, "r") as f:
                st.session_state.docs_data = json.load(f)
            return True
        except FileNotFoundError:
            return False
    return True


def display_search_results(results, query_time):
    st.write(f"Found {len(results)} results ({query_time:.3f} seconds)")
    
    for rank, result in enumerate(results, 1):
        with st.expander(f"{rank}. {result.url} (Score: {result.score:.3f})"):
            snippet = f"Matched terms: {', '.join(result.matched_terms)}"
            st.markdown(snippet)


def cleanup():
    if 'file_handler' in st.session_state:
        st.session_state.file_handler.__exit__(None, None, None)


def main():
    st.title("Search Engine")
    
    # Sidebar / Index
    st.sidebar.header("Configuration")
    data_dir = st.sidebar.selectbox(
        "Select Data Directory",
        [TEST_DIR, ANALYST_DIR, DEV_DIR],
        index=2
    )
    
    st.sidebar.header("Index Controls")
    col1, col2 = st.sidebar.columns([1, 1])

    with col1:
        if st.button("🏗️ Build Index 🛠️"):
            with st.spinner("Building index..."):
                indexer = Indexer(data_dir)
                
                progress_text = st.sidebar.empty()
                progress_bar = st.sidebar.progress(0)
                
                def update_progress(percent):
                    progress_bar.progress(percent / 100)
                    progress_text.text(f"Processing... {percent:.1f}%")
                
                def custom_print(text):
                    progress_text.text(text)
                
                indexer._print = custom_print
                indexer.set_progress_callback(update_progress)
                
                indexer.build_index()
                indexer.save_index()
                
                progress_text.text("Completed!")
                progress_bar.progress(100)
                st.sidebar.success("Index built successfully!")

    with col2:
        if st.button("🔄 Reload Data 🔄", help="Reload data"):
            st.session_state.pop('index_data', None)
            st.session_state.pop('docs_data', None)
            st.experimental_rerun()

    with st.sidebar.expander("Index Statistics"):                
        if load_json_data():
            stats_text = f"""
            📊 Index Statistics\n
            • Total documents: {len(st.session_state.docs_data)}\n
            • Total unique terms: {len(st.session_state.index_data)}\n
            • Index size: {Path(INDEX_FILE).stat().st_size / 1024:.2f} KB
            """
            st.info(stats_text)
        else:
            st.error("No index file found. Please build the index first.")

    # Search
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = SearchEngine()
        
    # Initialize FileHandler
    if 'file_handler' not in st.session_state:
        st.session_state.file_handler = FileHandler(INDEX_PEEK_FILE, INDEX_MAP_FILE)
        st.session_state.file_handler.__enter__()

    # Search interface
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("Enter your search query:")

    with col2:
        max_results = st.number_input("Max results", 5, 100, 10)
        
    if query:
        if load_json_data():
            with st.spinner("Searching..."):
                start_time = time.time()
                
                # Perform search with FileHandler
                results = st.session_state.search_engine.search(
                    query, 
                    max_results,
                    st.session_state.file_handler
                )
                
                query_time = time.time() - start_time
                display_search_results(results, query_time)             
        else:
            st.error("Search index not found. Please build the index first.")
    else:
        st.info("Enter a search query to find relevant documents")

if __name__ == "__main__":
    main()