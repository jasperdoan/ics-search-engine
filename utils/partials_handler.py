import json
import pickle
import time

from pathlib import Path

from utils.constants import RANGE_DIR


def get_term_partial_path(term: str) -> str:
    if not term:
        return f"{RANGE_DIR}/index_misc.json"
    return f"{RANGE_DIR}/index_{term[0].lower()}.json"



def convert_json_to_pickle():
    """Convert all JSON index files to pickle format"""
    range_dir = Path(RANGE_DIR)
    pickle_dir = Path(RANGE_DIR) / "pickle"
    pickle_dir.mkdir(exist_ok=True)
    
    print("Converting JSON indexes to pickle format...")
    
    total_files = len(list(range_dir.glob("*.json")))
    converted = 0
    
    start_time = time.time()
    
    for json_file in range_dir.glob("*.json"):
        if json_file.name.startswith("index_"):
            pickle_path = pickle_dir / f"{json_file.stem}.pkl"
            
            # Load JSON
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Save as pickle
            with open(pickle_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            converted += 1
            print(f"Converted {json_file.name} -> {pickle_path.name} ({converted}/{total_files})")
    
    end_time = time.time()
    print(f"\nConversion completed in {end_time - start_time:.2f} seconds")
    print(f"Files converted: {converted}")



def delete_all_pickles():
    """Delete all pickle files in the pickle directory"""
    pickle_dir = Path(RANGE_DIR) / "pickle"
    for pkl_file in pickle_dir.glob("*.pkl"):
        pkl_file.unlink()
    print("Deleted all pickle files")