"""
ListingSummarizer — Week 8 deliverable.

Extractive 2-3 sentence summarizer for MLS listing remarks. Follows the
starter algorithm from the project brief: tokenize the remarks into
sentences, score each by entity mentions and position, return top-N in
their original order so the summary reads naturally.

Bugfixes vs the literal starter code:
  - Word-boundary matching for numeric entities (so '3' inside '$300,000'
    doesn't count as a bedroom mention)
  - Iterates over all entities the EntityExtractor produces (bedrooms,
    bathrooms, sqft, price, amenities) rather than just bedrooms+pool
  - Strips periods from abbreviations like 'sq. ft.' before tokenizing
    (otherwise NLTK splits sentences mid-phrase)

Designed to consume the output of EntityExtractor.extract_all(), which
returns: bedrooms, bathrooms, price, sqft, amenities.
"""

import re
import math
import os
import nltk


def _ensure_nltk():
    """Download punkt tokenizer on first use. Safe to call repeatedly."""
    for resource in ('punkt_tab', 'punkt'):
        try:
            nltk.data.find(f'tokenizers/{resource}')
            return
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
                return
            except Exception:
                continue


class ListingSummarizer:
    """Extractive summarizer for real-estate listing remarks."""

    def __init__(self, num_sentences=2):
        """
        Args:
            num_sentences: How many sentences the summary should contain.
                Default is 2 to match the starter brief; pass 3 for fuller
                summaries when more context is desired.
        """
        _ensure_nltk()
        self.num_sentences = num_sentences

    @staticmethod
    def _is_present(value):
        """Treat None and NaN as missing. Everything else (including 0) is present."""
        if value is None:
            return False
        if isinstance(value, float) and math.isnan(value):
            return False
        return True

    @staticmethod
    def _normalize_abbreviations(text):
        """
        Pre-process the text to stop NLTK from splitting on abbreviation periods.
        Without this, 'offering 3,015 sq. ft. of living space' becomes two
        bad fragments: 'offering 3,015 sq.' and 'ft. of living space'.
        """
        replacements = [
            (r'\bsq\.\s*ft\.', 'sqft'),
            (r'\bSq\.\s*Ft\.', 'sqft'),
            (r'\bSQ\.\s*FT\.', 'sqft'),
            (r'\bsq\.', 'sq'),
            (r'\bft\.', 'ft'),
            (r'\bSt\.', 'St'),
            (r'\bAve\.', 'Ave'),
            (r'\bBlvd\.', 'Blvd'),
            (r'\bD\.R\.', 'DR'),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        return text

    def extractive_summary(self, remarks, entities, num_sentences=None):
        """
        Produce an extractive summary of `remarks` using `entities` for scoring.

        Args:
            remarks: The raw listing description (string).
            entities: Dict from EntityExtractor.extract_all() with keys
                bedrooms, bathrooms, price, sqft, amenities.
            num_sentences: Override the default sentence count for this call.

        Returns:
            A string containing the top-N sentences in their original order.
            Returns "" if remarks is empty or unusable.
        """
        if not remarks or not isinstance(remarks, str):
            return ""

        n = num_sentences if num_sentences is not None else self.num_sentences

        # Clean and normalize before tokenizing
        cleaned = re.sub(r'\s+', ' ', remarks).strip()
        cleaned = self._normalize_abbreviations(cleaned)
        if not cleaned:
            return ""

        sentences = nltk.sent_tokenize(cleaned)
        if not sentences:
            return ""

        # If listing has fewer sentences than requested, return all of them
        if len(sentences) <= n:
            return ' '.join(sentences)

        # Score each sentence by entity mentions and position
        entities = entities or {}
        scores = []
        for i, sent in enumerate(sentences):
            score = 0
            sent_lower = sent.lower()

            # First sentence bonus (the headline)
            if i == 0:
                score += 2

            # Numeric entity mentions — word boundary prevents false matches
            for key in ('bedrooms', 'bathrooms', 'sqft'):
                value = entities.get(key)
                if self._is_present(value):
                    if isinstance(value, float) and value.is_integer():
                        num_str = str(int(value))
                    else:
                        num_str = str(value)
                    if re.search(rf'\b{re.escape(num_str)}\b', sent):
                        score += 1

            # Price typically shows up as $XXX,XXX
            if self._is_present(entities.get('price')) and '$' in sent:
                score += 1

            # Amenity hits — flat scoring (matches starter code style)
            amenities = entities.get('amenities') or []
            for amenity in amenities:
                if not isinstance(amenity, str):
                    continue
                if re.search(rf'\b{re.escape(amenity.lower())}\b', sent_lower):
                    score += 1

            scores.append((score, i, sent))

        # Pick top-N by score, then restore original order using the index
        top = sorted(scores, key=lambda x: x[0], reverse=True)[:n]
        top_in_order = sorted(top, key=lambda x: x[1])
        return ' '.join(s for _, _, s in top_in_order)


if __name__ == "__main__":
    # Quick smoke test using your real extraction output
    import pandas as pd
    import ast

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_dir, 'results', 'extraction_results.csv')

    df = pd.read_csv(csv_path)
    summarizer = ListingSummarizer(num_sentences=2)

    for _, row in df.head(3).iterrows():
        amenities = ast.literal_eval(row['amenities']) if isinstance(row['amenities'], str) else []
        entities = {
            'bedrooms': row['bedrooms'],
            'bathrooms': row['bathrooms'],
            'price': row['price'],
            'sqft': row['sqft'],
            'amenities': amenities,
        }
        summary = summarizer.extractive_summary(row['remarks'], entities)
        print("=" * 60)
        print("ENTITIES:", {k: v for k, v in entities.items() if k != 'amenities'})
        print("SUMMARY:", summary)