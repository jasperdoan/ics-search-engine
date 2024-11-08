# WORDS
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 
    "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 
    'but', 'by', 'can', "can't", 'cannot', 'com', 'could', "couldn't", 'did', "didn't", 'do',
    'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'else', 'ever', 'few', 'for', 
    'from', 'further', 'get', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', 
    'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'm", 
    'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', 
    "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 
    'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", 
    "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the',
    'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they',
    "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under',
    'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
    "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while',
    'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you',
    "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves'
    }

# DIRECTORY
TEST_DIR = "./TEST"
ANALYST_DIR = "./ANALYST"
DEV_DIR = "./DEV"

# THRESHOLDS
SIMILARITY_THRESHOLD = 0.85
MAX_INDEX_SIZE_BYTES = 5 * 1024 * 1024
RANGE_SPLITS = [
    ('a', 'c'), ('d', 'f'), ('g', 'i'), ('j', 'l'),
    ('m', 'o'), ('p', 'r'), ('s', 'u'), ('v', 'z')
    ]

# FILE PATHS
PARTIAL_DIR = "partial_indexes"
RANGE_DIR = "range_indexes"
FULL_ANALYTICS_DIR = "full_analytics"
DOCS_FILE = f"{FULL_ANALYTICS_DIR}/documents.json" 
INDEX_FILE = f"{FULL_ANALYTICS_DIR}/index.json"

# TAGS
TAG_WEIGHTS = {
    'title': 1.0,
    'h1': 0.8,
    'h2': 0.6,
    'h3': 0.4,
    'b': 0.2,
    'strong': 0.2
}