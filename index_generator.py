import json

from pathlib import Path
from typing import Dict

from utils.constants import INDEX_FILE, INDEX_PEEK_FILE, INDEX_MAP_FILE

class IndexGenerator:
    """Handles generation of secondary index files for efficient search"""

    def __init__(self, index_path: str, output_txt: str, output_json: str):
        self.index_path = Path(index_path)
        self.output_txt = Path(output_txt) 
        self.output_json = Path(output_json)


    def generate_txt_index(self) -> None:
        """Convert JSON index to text format with term:postings lines"""
        try:
            with open(self.index_path) as file:
                index_data = json.load(file)
                
            with open(self.output_txt, "w") as txt_file:
                for key, value in index_data.items():
                    txt_file.write(f"{key}: {value}\n")
        except FileNotFoundError:
            print(f"Error: Input file {self.index_path} not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.index_path}")


    def generate_seek_positions(self) -> Dict[str, int]:
        """Generate dictionary mapping terms to file positions"""
        seek_positions = {}
        
        try:
            with open(self.output_txt, "r") as txt_file:
                while True:
                    seek_pos = txt_file.tell()
                    line = txt_file.readline()
                    
                    if not line:
                        break
                    
                    key = line.split(":")[0].strip()
                    seek_positions[key] = seek_pos
            return seek_positions
            
        except FileNotFoundError:
            print(f"Error: Text index file {self.output_txt} not found")
            return {}


    def save_secondary_index(self, seek_positions: Dict[str, int]) -> None:
        """Save term:position mapping to JSON file"""
        try:
            with open(self.output_json, "w") as json_file:
                json.dump(seek_positions, json_file, indent=4)
        except IOError:
            print(f"Error: Could not write to {self.output_json}")


    def generate(self) -> None:
        """Generate all index files"""
        self.generate_txt_index()
        seek_positions = self.generate_seek_positions()
        self.save_secondary_index(seek_positions)
        print("Index generation completed successfully!")


def main():
    generator = IndexGenerator(
        index_path=INDEX_FILE,
        output_txt=INDEX_PEEK_FILE,
        output_json=INDEX_MAP_FILE
    )
    generator.generate()

if __name__ == "__main__":
    main()