from collections import defaultdict
from typing import Dict, List
from functools import lru_cache

from utils.tokenizer import tokenize
from utils.constants import CONFIG


class TokenProcessor:
    @lru_cache(maxsize=CONFIG['max_cache_size'])
    def _tokenize_with_cache(self, text: str):
        return tokenize(text)

    def process_tokens(self, text: str, important_text: Dict[str, float]) -> Dict[str, tuple[int, float, List[int]]]:
        """Process tokens and track their positions"""
        freq_map = defaultdict(lambda: (0, 0.0, []))  # (freq, importance, positions)
        
        # Process regular text
        regular_tokens = self._tokenize_with_cache(text)
        
        for pos, token in enumerate(regular_tokens):
            freq, imp, positions = freq_map[token]
            freq_map[token] = (freq + 1, imp, positions + [pos])
        
        # Process important text with weights
        offset = len(regular_tokens)
        for text, weight in important_text.items():
            important_tokens = tokenize(text)
            
            for pos, token in enumerate(important_tokens, start=offset):
                freq, imp, positions = freq_map[token]
                freq_map[token] = (freq + 1, imp + weight, positions + [pos])
            offset += len(important_tokens)
            
        return freq_map