'''Utilities for cleaning and normalizing free-text real estate descriptions.'''

import re
import unicodedata


class TextCleaner:
    '''Normalize listing text so downstream extraction logic can work on consistent inputs.'''

    def __init__(self):
        '''Initialize the abbreviation map used during text normalization.'''
        self.abbrev_map = {
            'br': 'bedroom', 'ba': 'bathroom', 'sqft': 'square feet',
            'w/': 'with', 'w/o': 'without', 'mbr': 'master bedroom',
            'bd': 'bedroom', 'bed': 'bedroom', 'bth': 'bathroom',
            'fb': 'full bath', 'hb': 'half bath', 'lr': 'living room',
            'dr': 'dining room', 'kit': 'kitchen', 'fam': 'family room',
            'gar': 'garage', 'bsmt': 'basement', 'util': 'utility room',
            'fp': 'fireplace', 'fpl': 'fireplace', 'hwd': 'hardwood',
            'hw': 'hardwood', 'ac': 'air conditioning', 'a/c': 'air conditioning',
            'clst': 'closet', 'wd': 'wood', 'pvt': 'private',
            'att': 'attached', 'det': 'detached', 'remod': 'remodeled',
            'upgr': 'upgraded', 'ss': 'stainless steel', 'appl': 'appliances',
            'gran': 'granite', 'qtz': 'quartz', 'w/d': 'washer and dryer',
            'sq.ft.': 'square feet', 'sf': 'square feet', 'vws': 'views',
            'nbrhd': 'neighborhood'
        }

    def clean_text(self, text):
        '''Run the full normalization pipeline and return cleaned text.'''
        if not isinstance(text, str):
            return ""
        text = self.remove_HTML(text)
        text = self.normalize_unicode(text)
        text = self.lowercasing(text)
        text = self.normalize_prices(text)
        text = re.sub(r'(\d)([a-z])', r'\1 \2', text)
        text = self.expand_abbreviations(text)
        text = self.normalize_measurements(text)
        text = self.normalize_characters_and_punctuations(text)
        return text.strip()

    def normalize_prices(self, text):
        '''Expand shorthand prices such as 450k and 1.2m into full numbers.'''
        text = re.sub(r'(\d+)k', lambda m: str(int(m.group(1)) * 1000), text, flags=re.I)
        text = re.sub(
            r'(\d+\.?\d*)m',
            lambda m: str(int(float(m.group(1)) * 1000000)),
            text,
            flags=re.I
        )
        return text

    def expand_abbreviations(self, text):
        '''Replace known abbreviations with full terms from the abbreviation map.'''
        sorted_keys = sorted(self.abbrev_map.keys(), key=len, reverse=True)
        for abbrev in sorted_keys:
            full_word = self.abbrev_map[abbrev]
            pattern = r'(?<!\w)' + re.escape(abbrev) + r'(?!\w)'
            text = re.sub(pattern, full_word, text, flags=re.I)
        return text

    def remove_HTML(self, text):
        '''Strip HTML tags from text fields before further normalization.'''
        return re.sub(r'<[^>]+>', '', text, flags=re.I)

    def normalize_measurements(self, text):
        '''Standardize square-foot strings and remove thousand separators in numbers.'''
        return re.sub(
            r'([\d,]+)\s+square feet\b',
            lambda m: f"{m.group(1).replace(',', '')} square feet",
            text,
            flags=re.I
        )

    def lowercasing(self, text):
        '''Convert text to lowercase for case-insensitive downstream matching.'''
        if not isinstance(text, str):
            return ""
        return text.lower()

    def normalize_characters_and_punctuations(self, text):
        '''Collapse repeated punctuation and normalize all whitespace to single spaces.'''
        text = re.sub(r'([!*?.-])\1+', r'\1', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def normalize_unicode(self, text):
        '''Normalize unicode symbols and convert smart quotes to plain quotes.'''
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        return text

    def profile_column(self, df, column_name):
        '''Return null rate and average length statistics for a dataframe text column.'''
        null_count = df[column_name].isnull().sum()
        null_rate = null_count / len(df)

        valid_texts = df[column_name].dropna().astype(str)
        avg_length = valid_texts.apply(len).mean() if not valid_texts.empty else 0.0

        return {
            'null_rate': float(null_rate),
            'avg_length': float(avg_length)
        }
