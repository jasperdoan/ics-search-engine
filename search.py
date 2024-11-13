import json
from typing import Dict, List, Union, Tuple
from components.index_manager import Posting
from utils.partials_handler import get_term_partial_path
import re
import time

SEARCH_KEYWORDS = {"AND"}  # differentiates "AND" for boolean search and "and, And, aNd..." as tokens


def load_postings(file_path: str) -> Dict[str, List[Posting]]:
    with open(file_path, 'r') as file:
        data = json.load(file)

    postings_dict = {}
    for term, postings_list in data.items():
        postings = [
            Posting(doc_id=post[0], frequency=post[1], importance=post[2], tf_idf=post[3])
            for post in postings_list
        ]
        postings_dict[term] = postings

    return postings_dict

# return query as list of tokens
def process_query(search_query: str) -> List:
    tokens = re.findall(r'\b\w+\b', search_query)
    unique_tokens = set()
    processed_tokens = []
    
    for token in tokens:
        processed_token = token if token.upper() in SEARCH_KEYWORDS else token.lower()
        # Add only unique tokens
        if processed_token not in unique_tokens:
            unique_tokens.add(processed_token)
            processed_tokens.append(processed_token)

    return processed_tokens

# get results from postings_dict
def fetch_results(search_tokens: List) -> Dict:
    all_results = {}

    for token in search_tokens:
        if token not in SEARCH_KEYWORDS:
            all_results[token] = postings_dict[token]

    return all_results

# return list of lists: each list is keywords connected by an AND
def get_groups(search_tokens: List[str]) -> List[List[str]]:
    result = []
    current_group = []
    last_was_and = True
    
    for token in search_tokens:
   
        if token == "AND":
            last_was_and = True
            continue  
        
        if last_was_and:
            current_group.append(token)
            last_was_and = False

        else:
            result.append(current_group)
            current_group = [token]

    result.append(current_group)
    return result





def process_results(groups: List[List[str]]) -> List[set]:
    result = []
    
    for group in groups:
        common_doc_ids = None
        
        for keyword in group:
            partial_path = get_term_partial_path(keyword)

            postings = load_postings(partial_path)[keyword]

            doc_ids = {posting.doc_id for posting in postings}
            
            if common_doc_ids is None:
                common_doc_ids = doc_ids 
            else:
                common_doc_ids &= doc_ids

        result.append(common_doc_ids)
    
    return result



def main():

    start_time = time.time()

    search_query = "research AND student colleg"
    search_tokens = process_query(search_query)
    groups = get_groups(search_tokens)
    
    results = process_results(groups)
    print(results)

    end_time = time.time()
    elapsed_time_ms = (end_time - start_time)
    print(f"\n\nExecution Time: {elapsed_time_ms:.3f} seconds")


if __name__ == "__main__":
    main()