from scripts.meaningful_taxonomy_json_builder import taxonomy_data
import re

class EntityExtractor:
    def __init__(self):
        self.amenity_terms = []
        for category_terms in taxonomy_data.values():
            self.amenity_terms.extend(category_terms)
            
    def extract_bedrooms(self, text):
        patterns = [r'(\d+)\s*(?:bed|br|bedroom)s?', r'(\d+)bd']
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        return None

    def extract_price(self, text):
        match = re.search(r'\$?(\d{5,})', text)
        return int(match.group(1)) if match else None
    
    def extract_bathrooms(self, text):
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|bathroom|ba)s?', text, re.I)
        return float(match.group(1)) if match else None
    
    def extract_sqft(self, text):
        match = re.search(r'([\d,]+)\s*(?:sqft|sq\s*ft|square\s*feet)', text, re.I)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def extract_amenities(self, text):
        found = []
        for amenity in self.amenity_terms:
            if re.search(rf'\b{amenity}\b', text, re.I):
                found.append(amenity)
        return found

    def extract_all(self, text):
        return {
            'bedrooms': self.extract_bedrooms(text),
            'bathrooms': self.extract_bathrooms(text),
            'price': self.extract_price(text),
            'sqft': self.extract_sqft(text),
            'amenities': self.extract_amenities(text)
        }

    def extract_spans(self, text):
        entities = []
        
        num_pattern = r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
        
        bed_patterns = [rf'{num_pattern}\s*-?\s*(?:bed|br|bedroom)s?', r'(\d+)bd']
        for pattern in bed_patterns:
            for match in re.finditer(pattern, text, re.I):
                entities.append({"start": match.start(), "end": match.end(), "label": "BEDROOMS"})
                
        bath_pattern = rf'({num_pattern}(?:\.\d+)?)\s*-?\s*(?:bath|bathroom|ba)s?'
        for match in re.finditer(bath_pattern, text, re.I):
            entities.append({"start": match.start(), "end": match.end(), "label": "BATHROOMS"})

        for match in re.finditer(r'\$?(\d{5,})', text):
            entities.append({"start": match.start(), "end": match.end(), "label": "PRICE"})

        for match in re.finditer(r'([\d,]+)\s*(?:sqft|sq\s*ft|square\s*feet)', text, re.I):
            entities.append({"start": match.start(), "end": match.end(), "label": "SQFT"})

        for amenity in self.amenity_terms:
            for match in re.finditer(rf'\b{amenity}\b', text, re.I):
                entities.append({"start": match.start(), "end": match.end(), "label": "AMENITY"})

        return entities