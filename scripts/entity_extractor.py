import re
import json 

class EntityExtractor:
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
    # Added \.? to handle "sq. ft." and "sqft"
        pattern = r'([\d,]+)\s*(?:sq\.?\s*ft\.?|sqft|sf|square\s*feet)'
        match = re.search(pattern, text, re.I)
        if match:
            raw_value = match.group(1).replace(',', '').strip()
            if raw_value.isdigit():
                return int(raw_value)
        return None
    
    def extract_bathrooms(self, text):
    # Added \-? to allow for "2.5-bath" or "2-ba"
        pattern = r'(\d+(?:\.\d+)?)\s*\-?\s*(?:bath|ba|bathroom)s?'
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1))
        return None
        
    def extract_price(self, text):
    # Matches $ followed by digits and commas
        match = re.search(r'\$\s?([\d,]+)', text)
        if match:
            raw_value = match.group(1).replace(',', '').strip()
            if raw_value.isdigit():
                return int(raw_value)
        return None
    
    def __init__(self, taxonomy_path='data/processed/taxonomy.json'):
        with open(taxonomy_path, 'r') as f:
            data = json.load(f)
            
            # List of junk words to ignore (optional but highly recommended for 85% F1)
            stop_words = {'and a', 'in the', 'with a', 'to the', 'of the', 'is a'}
            
            self.amenity_taxonomy = [
                item['term'] for item in data['terms'] 
                if item['term'] not in stop_words
            ]

    def extract_amenities(self, text):
        found_amenities = []
        for term in self.amenity_taxonomy:
            # \b ensures we match whole words only (prevents 'pool' matching 'spool')
            # re.escape handles terms with special characters
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