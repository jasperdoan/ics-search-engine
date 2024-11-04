import hashlib
from parser_utils import tokenize

class SimHash:
    def __init__(self, b=64):
        self.b = b  # Number of bits in the fingerprint

    def _hash_word(self, word):
        encoded_word = word.encode('utf-8') # Encode the word into bytes using UTF-8 encoding
        md5_hash = hashlib.md5()            # Create an MD5 hash object
        md5_hash.update(encoded_word)       # Update the hash object with the encoded word
        hex_digest = md5_hash.hexdigest()   # Get the hexadecimal digest of the hash
        hash_value = int(hex_digest, 16)    # Convert the hexadecimal digest to an integer with base 16
        return bin(hash_value)[2:].zfill(self.b)[-self.b:]  # Convert hash value to binary and ensure it is b bits long

    def _calculate_frequencies(self, tokens):
        # Calculate word frequencies
        freq = {}
        for token in tokens:
            if token in freq:
                freq[token] += 1
            else:
                freq[token] = 1
        return freq


    def compute_simhash(self, text):
        tokens = tokenize(text)
        frequencies = self._calculate_frequencies(tokens)
        
        V = [0] * self.b
        
        for word, weight in frequencies.items():
            hash_value = self._hash_word(word)
            for i in range(self.b):
                if hash_value[i] == '1':
                    V[i] += weight
                else:
                    V[i] -= weight
        
        fingerprint = ''.join(['1' if v > 0 else '0' for v in V])
        return fingerprint

    def hamming_distance(self, hash1, hash2):
        # Calculate the Hamming distance between two hashes
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def similarity(self, text1, text2):
        hash1 = self.compute_simhash(text1)
        hash2 = self.compute_simhash(text2)
        distance = self.hamming_distance(hash1, hash2)
        return 1 - distance / self.b

    def are_near_duplicates(self, text1, text2, threshold=0.8):
        return self.similarity(text1, text2) >= threshold
