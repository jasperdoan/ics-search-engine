from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from urllib.parse import urlparse
from constants import STOP_WORDS


# Do this first, that'll do something eval() to "materialize" the LazyCorpusLoader
next(nltk.corpus.wordnet.all_synsets())


def tokenize(text):
    """
    Tokenize the input text.

    This function uses NLTK's RegexpTokenizer to tokenize the text into words,
    converts them to lowercase, and removes single-character tokens.

    We want to tokenize the text for several reasons:
    - Helps in normalizing the text, for word frequency analysis, where you want to count all occurrences of a word regardless of its form.
    - Reduce the number of unique words in your dataset
    """
    # Tokenize the text into words, re_tokens = ['word1', 'word2', ...]
    re_tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    re_tokens = re_tokenizer.tokenize(text.lower())

    # Remove stop words from the tokens 
    tokens = [token for token in re_tokens if token not in STOP_WORDS]

    # Identify the base form of any verbs (pos="v") and lemmatize those tokens
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(w, pos="v") for w in re_tokens]

    # Remove single-character tokens
    return [token for token in tokens if len(token) != 1]