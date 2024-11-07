import re

from dataclasses import dataclass
from bs4 import BeautifulSoup
from utils.simhash import SimHash
from typing import Tuple, Dict

from utils.constants import TAG_WEIGHTS

@dataclass
class Document:
    url: str
    content: str
    doc_id: int
    simhash: str = ""

class DocumentProcessor:
    def __init__(self):
        self.simhasher = SimHash()

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text by removing special characters"""
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def soupify(self, data: dict) -> Tuple[BeautifulSoup, str]:
        """Create BeautifulSoup object and extract clean text"""
        soup = BeautifulSoup(data.get('content', ''), 'html.parser')
        
        if data.get('encoding', '').lower() == 'utf-8':
            paragraphs = soup.find_all('p')
            if paragraphs:
                text = ' '.join(p.get_text().strip() for p in paragraphs)
                return soup, self._clean_text(text)
        
        return soup, self._clean_text(soup.get_text())

    def extract_important_text(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Extract text from important HTML tags with their weights"""
        weighted_text = {}
        for tag, weight in TAG_WEIGHTS.items():
            elements = soup.find_all(tag)
            for element in elements:
                text = element.get_text().strip()
                weighted_text[text] = weight
        return weighted_text

    def create_document(self, data: dict, text: str, doc_id: int) -> Document:
        """Create a new Document instance"""
        simhash = self.simhasher.compute_simhash(text)
        return Document(
            url=data['url'],
            content=text,
            doc_id=doc_id,
            simhash=simhash
        )

    def is_near_duplicate(self, simhash: str, existing_docs: Dict[int, Document], threshold: float) -> bool:
        """Check if document is a near-duplicate"""
        for existing_doc in existing_docs.values():
            similarity_score = 1 - self.simhasher.hamming_distance(simhash, existing_doc.simhash) / self.simhasher.b
            if similarity_score >= threshold:
                print(f"\tNear-duplicate document detected to {existing_doc.doc_id}, being {100*similarity_score:.2f}% similar")
                return True
        return False