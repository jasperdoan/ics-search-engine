from utils.constants import RANGE_DIR, RANGE_SPLITS
    
def get_term_partial_path(term: str) -> str:
    partial_index = ""

    if not term:
        partial_index = "misc"
    
    first_char = term[0].lower()
    if not first_char.isalpha():
        partial_index = "misc"
        
    for start, end in RANGE_SPLITS:
        if start <= first_char <= end:
            partial_index = f"{start}_{end}"

    return f"{RANGE_DIR}/index_{partial_index}.json"