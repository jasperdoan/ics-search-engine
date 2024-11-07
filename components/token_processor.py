from collections import defaultdict
from typing import Dict, List
from utils.tokenizer import tokenize

class TokenProcessor:
    def process_tokens(self, text: str, important_text: str) -> Dict[str, tuple[int, int]]:
        """Process regular and important tokens to create frequency map"""
        freq_map = defaultdict(lambda: (0, 0))
        
        # Process regular text
        regular_tokens = tokenize(text)
        print(f"\tRegular tokens: {len(regular_tokens)}")
        
        for token in regular_tokens:
            count, imp = freq_map[token]
            freq_map[token] = (count + 1, imp)
            
        # Process important text
        important_tokens = tokenize(important_text)
        print(f"\tImportant tokens: {len(important_tokens)}")
        
        for token in important_tokens:
            count, imp = freq_map[token]
            freq_map[token] = (count * 2 if count > 0 else 1, imp + 1)
            
        return freq_map