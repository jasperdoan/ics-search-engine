from collections import defaultdict
from typing import Dict, List, Tuple
from functools import lru_cache

from utils.tokenizer import tokenize
from utils.constants import CONFIG


class TokenProcessor:
    @lru_cache(maxsize=CONFIG['max_cache_size'])
    def _tokenize_with_cache(self, text: str):
        return tokenize(text)

    def process_tokens(self, text: str, important_text: Dict[str, float]) -> Dict[str, Tuple[int, float, List[int]]]:
        """Process tokens and track their positions"""
        freq_map = defaultdict(lambda: (0, 0.0, []))  # (freq, importance, positions)
        
        # Process regular text
        regular_tokens = self._tokenize_with_cache(text)
        
        for pos, token in enumerate(regular_tokens):
            freq, imp, positions = freq_map[token]
            freq_map[token] = (freq + 1, imp, positions + [pos])
        
        # Process important text with weights
        for text, weight in important_text.items():
            important_tokens = self._tokenize_with_cache(text)
            
            for token in important_tokens:
                freq, imp, positions = freq_map[token]
                freq_map[token] = (freq + 1, imp + weight, positions)
            
        return freq_map