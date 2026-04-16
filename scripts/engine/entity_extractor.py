import re
import json
import os

class EntityExtractor:
    def __init__(self, taxonomy_path=None):
        """
        Initializes the extractor. If no taxonomy_path is provided, 
        it calculates the path relative to this script's location.
        """
        if taxonomy_path is None:
            # __file__ is scripts/engine/entity_extractor.py
            # 1. os.path.dirname(__file__) -> scripts/engine
            # 2. dirname of that -> scripts
            # 3. dirname of that -> project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            taxonomy_path = os.path.join(base_dir, 'data', 'processed', 'taxonomy.json')

        try:
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # List of junk words to ignore
                stop_words = {'and a', 'in the', 'with a', 'to the', 'of the', 'is a'}
                
                self.amenity_taxonomy = [
                    item['term'] for item in data['terms'] 
                    if item['term'].lower() not in stop_words
                ]
        except FileNotFoundError:
            print(f"Warning: Taxonomy file not found at {taxonomy_path}")
            self.amenity_taxonomy = []

    def extract_bedrooms(self, text):
        patterns = [
            r'(\d+)\s*\-?\s*(?:bed|br|bedroom)s?',
            r'(\d+)bd'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        return None
    
    def extract_sqft(self, text):
        pattern = r'([\d,]+)\s*(?:sq\.?\s*ft\.?|sqft|sf|square\s*feet)'
        match = re.search(pattern, text, re.I)
        if match:
            raw_value = match.group(1).replace(',', '').strip()
            if raw_value.isdigit():
                return int(raw_value)
        return None
    
    def extract_bathrooms(self, text):
        pattern = r'(\d+(?:\.\d+)?)\s*\-?\s*(?:bath|ba|bathroom)s?'
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1))
        return None
        
    def extract_price(self, text):
        match = re.search(r'\$\s?([\d,]+)', text)
        if match:
            raw_value = match.group(1).replace(',', '').strip()
            if raw_value.isdigit():
                return int(raw_value)
        return None

    def extract_amenities(self, text):
        if not text or not isinstance(text, str):
            return []
        found_amenities = []
        for term in self.amenity_taxonomy:
            pattern = rf'\b{re.escape(term)}\b'
            if re.search(pattern, text, re.I):
                found_amenities.append(term)
        return found_amenities

    def extract_all(self, text):
        return {
            'bedrooms': self.extract_bedrooms(text),
            'bathrooms': self.extract_bathrooms(text),
            'price': self.extract_price(text),
            'sqft': self.extract_sqft(text),
            'amenities': self.extract_amenities(text)
        }