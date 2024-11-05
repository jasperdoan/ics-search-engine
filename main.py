import streamlit as st
import json
from pathlib import Path
from indexer import Indexer

st.set_page_config(
    page_title='CS121 A3 Search Engine',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='auto'
    )

def main():
    st.title("Search Engine")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    data_dir = st.sidebar.selectbox(
        "Select Data Directory",
        ["./TEST", "./DEV", "./ANALYST"],
        index=0
    )
    
    # Main content
    st.header("Index Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Build Index"):
            with st.spinner("Building index..."):
                indexer = Indexer(data_dir)
                
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
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
                st.success("Index built successfully!")

    with col2:
        if st.button("View Statistics"):
            try:
                with open("index.json", "r") as f:
                    data = json.load(f)
                    
                stats_text = f"""
                📊 Index Statistics\n
                • Total documents: {len(data['documents'])}\n
                • Total unique terms: {len(data['index'])}\n
                • Index size: {Path('index.json').stat().st_size / 1024:.2f} KB
                """
                st.info(stats_text)
                
            except FileNotFoundError:
                st.error("No index file found. Please build the index first.")

    # Placeholder for future search functionality
    st.header("Search")
    st.info("Search functionality coming soon!")
    query = st.text_input("Enter your search query:")
    if query:
        st.warning("Search feature is not implemented yet.")

if __name__ == "__main__":
    main()