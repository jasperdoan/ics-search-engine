from utils.constants import RANGE_DIR

def get_term_partial_path(term: str) -> str:
    if not term:
        return f"{RANGE_DIR}/index_misc.json"
    return f"{RANGE_DIR}/index_{term[0].lower()}.json"