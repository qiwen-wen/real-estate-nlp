import re
import pandas as pd
import unicodedata
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
        return {
            'null_rate': df[column_name].isnull().mean(),
            'avg_length': df[column_name].str.len().mean(),
            'common_terms': self.extract_top_ngrams(df[column_name]),
            'price_mentions': df[column_name].str.contains(r'\$\d').sum(),
            'has_html': df[column_name].str.contains('<').sum(),
            'common_abbreviations': self.detect_abbreviations(df[column_name])
        }

    def clean_text(self, text):
        if not isinstance(text, str): return ""
        
        # 1. Normalize Unicode FIRST to strip accents (é -> e)
        text = self.normalize_unicode(text)
        
        # 2. Strip HTML
        text = self.strip_html(text)
        
        # 3. Lowercase everything
        text = text.lower()
        
        # 4. Normalize prices BEFORE space injection
        text = self.normalize_prices(text)
        
        # 5. Fix measurements (10ac -> 10 acres)
        text = self.normalize_measurements(text)
        
        # 6. Force space between numbers and letters (3.5ba -> 3.5 ba)
        text = re.sub(r'([0-9\.]+)([a-zA-Z]+)', r'\1 \2', text)
        
        # 7. Expand abbreviations
        text = self.expand_abbreviations(text)
        
        # 8. Cleanup
        text = text.replace('/', ' ')
        return re.sub(r'\s+', ' ', text).strip()
    
    def normalize_prices(self, text):
        # 450k → 450000
        text = re.sub(r'(\d+)k', lambda m: str(int(m.group(1))*1000), text,
        flags=re.I)
        # 1.2m → 1200000
        text = re.sub(r'(\d+\.?\d*)m', lambda m:
        str(int(float(m.group(1))*1000000)), text, flags=re.I)
        return text
    
    def normalize_unicode(self, text):
        if not isinstance(text, str): return ""
        # NFKD decomposes characters (é becomes e + accent)
        # then .encode('ascii', 'ignore') throws away the accent
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    
    def normalize_measurements(self, text):
    # Handle '10ac' -> '10 acres' specifically
        text = re.sub(r'(\d+)\s?ac\b', r'\1 acres', text, flags=re.I)
    
    # Existing comma removal logic
        text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
        return text
    
    def extract_top_ngrams(self, series, n=2, top_k=5):
        """Finds the most common phrases (n-grams) in the text."""
        # Fill NaN values and join all text into one giant string
        text = " ".join(series.fillna('').astype(str)).lower()
        # Basic tokenization
        words = re.findall(r'\b\w+\b', text)
        # Create n-grams (defaulting to bigrams like 'and a', 'in the')
        ngrams = zip(*[words[i:] for i in range(n)])
        ngram_counts = Counter(ngrams).most_common(top_k)
        # Format them back into strings
        return [" ".join(gram) for gram, count in ngram_counts]
    
    def detect_abbreviations(self, series):
        """Finds potential abbreviations (short words) for the profiling report."""
        # Combine all text, lowercase it, and find all words
        text = " ".join(series.fillna('').astype(str)).lower()
        words = re.findall(r'\b\w{2,4}\b', text)
        
        # Filter out common stop words so you only see potential abbreviations
        stop_words = {'the', 'and', 'with', 'for', 'this', 'that', 'from'}
        abbrev_candidates = [w for w in words if w not in stop_words]
        
        # Use Counter to get the top 10 most frequent candidates
        return Counter(abbrev_candidates).most_common(10)

    
    def expand_abbreviations(self, text):
    # Sort keys by length (longest first) so 'w/o' is caught before 'w/'
        sorted_keys = sorted(self.abbrev_map.keys(), key=len, reverse=True)
    
        for abbrev in sorted_keys:
            full_form = self.abbrev_map[abbrev]
        # Use a regex that handles boundaries but allows slashes
            pattern = rf'(?<!\w){re.escape(abbrev)}(?!\w)'
            text = re.sub(pattern, full_form, text, flags=re.I)
        return text
    
    def strip_html(self, text):
        """Remove HTML tags like <b> or <br/> from the text."""
        if not isinstance(text, str): return ""
        # This regex looks for anything inside <> and replaces it with a space
        clean = re.sub(r'<.*?>', ' ', text)
        # Also handle common HTML entities like &nbsp;
        clean = re.sub(r'&[a-z]+;', ' ', clean)
        return clean

if __name__ == "__main__":
    # Instantiate the cleaner class
    cleaner = TextCleaner()

    # 1. Load your specific file directly
    df = pd.read_csv('data/processed/listing_sample.csv')

    # 2. Run the profiling report (Required Deliverable)
    print("--- DATA PROFILING REPORT ---")
    profile = cleaner.profile_column(df, 'remarks')
    for key, val in profile.items():
        print(f"{key}: {val}")

    # 3. Apply the cleaning pipeline to the 'remarks' column
    # This creates a new column so you can compare before/after
    df['cleaned_remarks'] = df['remarks'].apply(cleaner.clean_text)

    # 4. Save the final cleaned version
    df.to_csv('data/processed/cleaned_listings.csv', index=False)
    
    print("\nSuccess! Cleaned dataset saved to data/processed/cleaned_listings.csv")
    
    # Show the first 5 rows to verify
    print("\n--- SAMPLE OUTPUT ---")
    print(df[['remarks', 'cleaned_remarks']].head())