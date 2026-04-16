import re
import json
import os

try:
    from .entity_extractor import EntityExtractor
except ImportError:
    # Fallback for running the script directly
    from entity_extractor import EntityExtractor

class SignalExtractor:
    def __init__(self, taxonomy_path=None, entity_extractor=None):
        """
        Initializes the signal logic. 
        Calculates taxonomy path relative to the project root if not provided.
        """
        if taxonomy_path is None:
            # Navigate up from scripts/engine/ to the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            taxonomy_path = os.path.join(base_dir, 'data', 'processed', 'taxonomy.json')

        try:
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                self.raw_taxonomy = json.load(f).get('terms', [])
        except FileNotFoundError:
            print(f"Warning: Taxonomy not found at {taxonomy_path}")
            self.raw_taxonomy = []

        # Use provided extractor or create a new one intelligently
        self.extractor = entity_extractor or EntityExtractor(taxonomy_path=taxonomy_path)

    def _safe_int(self, val):
        """Safely converts strings/decimals to integers."""
        try:
            if val is None or str(val).strip() == '' or str(val).lower() == 'nan':
                return None
            return int(float(str(val).replace(',', '')))
        except (ValueError, TypeError):
            return None

    def _safe_float(self, val):
        """Safely converts strings to floats for bathrooms."""
        try:
            if val is None or str(val).strip() == '' or str(val).lower() == 'nan':
                return None
            return float(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return None

    def _filter_terms(self, matched_amenities, keywords):
        """Helper to group taxonomy terms into specific categories."""
        return [term for term in matched_amenities if any(k in term.lower() for k in keywords)]

    def extract_signals(self, listing_record):
        # Force string type for remarks to prevent float errors from NaN values
        remarks = str(listing_record.get('L_Remarks', ''))
        if remarks.lower() == 'nan':
            remarks = ''
        
        # 1. Use existing NLP logic
        entities = self.extractor.extract_all(remarks)
        matched = entities.get('amenities', [])

        # 2. ACCURACY FALLBACK: Use SQL columns if regex finds nothing
        # This pulls directly from the database record dictionary
        bedrooms = self._safe_int(entities.get('bedrooms') or listing_record.get('L_Keyword2'))
        bathrooms = self._safe_float(entities.get('bathrooms') or listing_record.get('LM_Dec_3'))
        price = self._safe_int(entities.get('price') or listing_record.get('L_SystemPrice'))
        sqft = self._safe_int(entities.get('sqft') or listing_record.get('LM_Int2_3'))

        return {
            'listing_id': listing_record.get('L_ListingID'),
            'entities': {
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'price': price,
                'sqft': sqft
            },
            'amenities': [t for t in matched if not any(k in t.lower() for k in ['view', 'access', 'modern', 'new', 'hoa', 'finance', 'cash'])],
            'condition_keywords': self._filter_terms(matched, ['modern', 'new', 'updated', 'renovated', 'remodel', 'masterfully', 'dramatic']),
            'financing_terms': self._filter_terms(matched, ['hoa', 'dues', 'income', 'financing', 'cash', 'exchange']),
            'location_features': self._filter_terms(matched, ['view', 'access', 'proximity', 'location', 'lot', 'canyon', 'hills', 'tucked'])
        }