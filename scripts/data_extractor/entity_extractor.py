'''Entity extraction helpers for structured fields in listing description text.'''

import os
import re
import sys

try:
    from scripts.data_loading.meaningful_taxonomy_json_builder import taxonomy_data
except ModuleNotFoundError:
    SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if SCRIPTS_DIR not in sys.path:
        sys.path.append(SCRIPTS_DIR)
    from data_loading.meaningful_taxonomy_json_builder import taxonomy_data


class EntityExtractor:
    '''Extract bedrooms, bathrooms, price, square footage, and amenities from text.'''

    def __init__(self):
        '''Flatten taxonomy terms into a searchable amenity list.'''
        self.amenity_terms = []
        for category_terms in taxonomy_data.values():
            self.amenity_terms.extend(category_terms)

    def extract_bedrooms(self, text):
        '''Extract bedroom count if bedroom-like patterns are present.'''
        patterns = [r'(\d+)\s*(?:bed|br|bedroom)s?', r'(\d+)bd']
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        return None

    def extract_price(self, text):
        '''Extract a five-plus digit numeric price from text.'''
        match = re.search(r'\$?(\d{5,})', text)
        return int(match.group(1)) if match else None

    def extract_bathrooms(self, text):
        '''Extract bathroom count, including decimal values such as 2.5 baths.'''
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|bathroom|ba)s?', text, re.I)
        return float(match.group(1)) if match else None

    def extract_sqft(self, text):
        '''Extract square-foot value from common square-foot patterns.'''
        match = re.search(r'([\d,]+)\s*(?:sqft|sq\s*ft|square\s*feet)', text, re.I)
        if match:
            return int(match.group(1).replace(',', ''))
        return None

    def extract_amenities(self, text):
        '''Return all taxonomy amenities that appear in the input text.'''
        found = []
        for amenity in self.amenity_terms:
            if re.search(rf'\b{re.escape(amenity)}\b', text, re.I):
                found.append(amenity)
        return found

    def extract_all(self, text):
        '''Extract all supported scalar entities and amenity matches in one pass.'''
        return {
            'bedrooms': self.extract_bedrooms(text),
            'bathrooms': self.extract_bathrooms(text),
            'price': self.extract_price(text),
            'sqft': self.extract_sqft(text),
            'amenities': self.extract_amenities(text)
        }

    def extract_spans(self, text):
        '''Extract span-level entities as start/end offsets plus a label.'''
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
            for match in re.finditer(rf'\b{re.escape(amenity)}\b', text, re.I):
                entities.append({"start": match.start(), "end": match.end(), "label": "AMENITY"})

        return entities
