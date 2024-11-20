from utils.constants import RANGE_DIR
    
def get_term_partial_path(term: str) -> str:
    partial_index = ""

    if not term:
        partial_index = "misc"
    
    first_char = term[0].lower()
    if not first_char.isalpha():
        partial_index = "misc"

    return f"{RANGE_DIR}/index_{first_char}.json"