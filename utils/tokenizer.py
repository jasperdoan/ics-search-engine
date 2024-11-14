import nltk

from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from urllib.parse import urlparse
from utils.constants import STOP_WORDS


def tokenize(text: str):
    """
    Tokenize and stem the input text.

    This function:
    1. Uses NLTK's RegexpTokenizer to tokenize text into words
    2. Converts to lowercase 
    3. Removes stop words
    4. Applies Porter stemming
    5. Removes single-character tokens
    """
    # Initialize Porter Stemmer
    stemmer = PorterStemmer()
    
    # Tokenize text into words
    re_tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    re_tokens = re_tokenizer.tokenize(text.lower())

    # Remove stop words and apply stemming
    tokens = [stemmer.stem(token) for token in re_tokens]

    # Remove single-character tokens
    return [token for token in tokens if len(token) != 1]


def query_tokenize(text: str):
    """
    Tokenize and stem query text with stop word removal.
    Used specifically for search queries.
    """
    # Initialize Porter Stemmer
    stemmer = PorterStemmer()
    
    # Tokenize text into words
    re_tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    re_tokens = re_tokenizer.tokenize(text.lower())

    # Remove stop words and apply stemming
    tokens = [stemmer.stem(token) for token in re_tokens if token.lower() not in STOP_WORDS]

    # Remove single-character tokens
    return [token for token in tokens if len(token) != 1]