import streamlit as st
import json

from pathlib import Path
from indexer import Indexer

from utils.constants import (
    TEST_DIR,
    ANALYST_DIR,
    DEV_DIR,
    DOCS_FILE,
    INDEX_FILE
)

st.set_page_config(
    page_title='CS121 A3 Search Engine',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='auto'
)

def main():
    st.title("Search Engine")
    
    # Sidebar
    st.sidebar.header("Configuration")
    data_dir = st.sidebar.selectbox(
        "Select Data Directory",
        [TEST_DIR, ANALYST_DIR, DEV_DIR],
        index=0
    )
    
    st.sidebar.header("Index Controls")
    if st.sidebar.button("Build Index"):
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

    with st.sidebar.expander("Index Statistics"):
        try:
            with open(INDEX_FILE, "r") as f:
                index_data = json.load(f)

            with open(DOCS_FILE, "r") as f:
                docs_data = json.load(f)
                
            stats_text = f"""
            📊 Index Statistics\n
            • Total documents: {len(docs_data)}\n
            • Total unique terms: {len(index_data)}\n
            • Index size: {Path('index.json').stat().st_size / 1024:.2f} KB
            """
            st.info(stats_text)
            
        except FileNotFoundError:
            st.error("No index file found. Please build the index first.")

    # Main content - Search
    query = st.text_input("Enter your search query:")
    if query:
        st.warning("Search feature is not implemented yet.")
    else:
        st.info("Enter a search query to find relevant documents")

if __name__ == "__main__":
    main()