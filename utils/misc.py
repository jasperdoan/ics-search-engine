import os
import ssl
import nltk



def set_up_ssl():
    """
    Set up SSL context to allow unverified HTTPS connections.
    This function is used to bypass SSL verification, which is necessary
    for downloading NLTK data in some environments where SSL verification
    might fail.
        Source: https://github.com/Thundelly/CS121-Web-Crawler/blob/8cd040bd0834597a8265d4ea4d27487d71ff6bd7/scraper.py#L180
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context



def download_nltk_library():
    """
    Download the NLTK 'wordnet' library if it is not already present.
    This function sets up the NLTK data path and downloads the 'wordnet'
    corpus if it is not already available in the specified directory.
    Provides short definitions and usage examples, and records various semantic relations.
    Need to perform lemmatization.
        Source: https://github.com/Thundelly/CS121-Web-Crawler/blob/8cd040bd0834597a8265d4ea4d27487d71ff6bd7/scraper.py#L180
    """
    if not os.path.exists('./nltk_data/corpora/'):
        os.makedirs('./nltk_data/corpora/')

    nltk.data.path.append('./nltk_data/')
    if not os.path.exists('./nltk_data/corpora'):
        set_up_ssl()
        nltk.download('wordnet', download_dir='./nltk_data/')