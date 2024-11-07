from collections import defaultdict
from typing import Dict, List
from utils.tokenizer import tokenize

class TokenProcessor:
    def process_tokens(self, text: str, important_text: Dict[str, float]) -> Dict[str, tuple[int, float]]:
        """Process regular and important tokens to create frequency map"""
        freq_map = defaultdict(lambda: (0, 0.0))
        
        # Process regular text
        regular_tokens = tokenize(text)
        print(f"\tRegular tokens: {len(regular_tokens)}")
        
        for token in regular_tokens:
            count, imp = freq_map[token]
            freq_map[token] = (count + 1, imp)
        
        # Process important text with weights
        for text, weight in important_text.items():
            important_tokens = tokenize(text)
            print(f"\tImportant tokens with weight {weight}: {important_tokens}")
            
            for token in important_tokens:
                count, imp = freq_map[token]
                # Add weight to importance score
                freq_map[token] = (count + 1, imp + weight)
        
        return freq_map