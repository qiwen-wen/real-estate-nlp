import re
import pandas as pd
import unicodedata
import os
from collections import Counter

class TextCleaner:
    def __init__(self):
        self.abbrev_map = {
            # Rooms & Areas
            'br': 'bedroom', 'ba': 'bathroom', 'mbr': 'master bedroom', 
            'kit': 'kitchen', 'fam rm': 'family room', 'din rm': 'dining room',
            'util': 'utility room', 'gar': 'garage', 'bsmt': 'basement',
            # Features
            'fplc': 'fireplace', 'hwd': 'hardwood', 'cpt': 'carpet',
            'gran': 'granite', 'ss': 'stainless steel', 'appls': 'appliances',
            'w/d': 'washer and dryer', 'hvac': 'heating ventilation and air conditioning',
            'ac': 'air conditioning', 'deck': 'deck', 'pattio': 'patio',
            # Measurements & Status
            'sqft': 'square feet', 'sq ft': 'square feet', 'sf': 'square feet',
            'acres': 'acres', 'lrg': 'large', 'updtd': 'updated',
            'remod': 'remodeled', 'mve-in': 'move-in', 'pos': 'possession',
            'w/': 'with', 'w/o': 'without', 'feat': 'features'
        }

    def profile_column(self, df, column_name):
        """Analyze what's actually in L_Remarks"""
        if column_name not in df.columns:
            return f"Error: Column {column_name} not found."
            
        return {
            'null_rate': df[column_name].isnull().mean(),
            'avg_length': df[column_name].str.len().mean(),
            'common_terms': self.extract_top_ngrams(df[column_name]),
            'price_mentions': df[column_name].str.contains(r'\$\d', na=False).sum(),
            'has_html': df[column_name].str.contains('<', na=False).sum(),
            'common_abbreviations': self.detect_abbreviations(df[column_name])
        }

    def clean_text(self, text):
        if not isinstance(text, str) or str(text).lower() == 'nan': 
            return ""
        
        text = self.normalize_unicode(text)
        text = self.strip_html(text)
        text = text.lower()
        text = self.normalize_prices(text)
        text = self.normalize_measurements(text)
        
        # Force space between numbers and letters (3.5ba -> 3.5 ba)
        text = re.sub(r'([0-9\.]+)([a-zA-Z]+)', r'\1 \2', text)
        
        text = self.expand_abbreviations(text)
        text = text.replace('/', ' ')
        return re.sub(r'\s+', ' ', text).strip()
    
    def normalize_prices(self, text):
        text = re.sub(r'(\d+)k', lambda m: str(int(m.group(1))*1000), text, flags=re.I)
        text = re.sub(r'(\d+\.?\d*)m', lambda m: str(int(float(m.group(1))*1000000)), text, flags=re.I)
        return text
    
    def normalize_unicode(self, text):
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    
    def normalize_measurements(self, text):
        text = re.sub(r'(\d+)\s?ac\b', r'\1 acres', text, flags=re.I)
        text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
        return text
    
    def extract_top_ngrams(self, series, n=2, top_k=5):
        text = " ".join(series.fillna('').astype(str)).lower()
        words = re.findall(r'\b\w+\b', text)
        ngrams = zip(*[words[i:] for i in range(n)])
        ngram_counts = Counter(ngrams).most_common(top_k)
        return [" ".join(gram) for gram, count in ngram_counts]
    
    def detect_abbreviations(self, series):
        text = " ".join(series.fillna('').astype(str)).lower()
        words = re.findall(r'\b\w{2,4}\b', text)
        stop_words = {'the', 'and', 'with', 'for', 'this', 'that', 'from'}
        abbrev_candidates = [w for w in words if w not in stop_words]
        return Counter(abbrev_candidates).most_common(10)

    def expand_abbreviations(self, text):
        sorted_keys = sorted(self.abbrev_map.keys(), key=len, reverse=True)
        for abbrev in sorted_keys:
            full_form = self.abbrev_map[abbrev]
            pattern = rf'(?<!\w){re.escape(abbrev)}(?!\w)'
            text = re.sub(pattern, full_form, text, flags=re.I)
        return text
    
    def strip_html(self, text):
        clean = re.sub(r'<.*?>', ' ', text)
        clean = re.sub(r'&[a-z]+;', ' ', clean)
        return clean

if __name__ == "__main__":
    cleaner = TextCleaner()

    # Dynamic path logic to find data folders from within scripts/engine/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(base_dir, 'data', 'interim', 'listing_sample.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_listings.csv')

    if os.path.exists(input_path):
        df = pd.read_csv(input_path)
        # Use 'remarks' or 'L_Remarks' depending on your file's columns
        target_col = 'remarks' if 'remarks' in df.columns else 'L_Remarks'
        
        print(f"--- DATA PROFILING REPORT ({target_col}) ---")
        profile = cleaner.profile_column(df, target_col)
        print(profile)

        df['cleaned_remarks'] = df[target_col].apply(cleaner.clean_text)
        df.to_csv(output_path, index=False)
        print(f"\nSuccess! Saved to {output_path}")
    else:
        print(f"Error: Could not find input file at {input_path}")