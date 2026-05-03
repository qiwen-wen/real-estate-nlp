import re
import os
import math
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


# Amenities that are genuinely informative for a buyer scanning summaries.
# Generic filler like "natural light" or "easy access" is intentionally excluded
# because nearly every listing mentions it — scoring them rewards fluff.
HIGH_VALUE_AMENITIES = {
    'pool', 'spa', 'hot tub', 'garage', 'car garage', 'view', 'ocean view',
    'mountain views', 'hardwood floors', 'granite countertops', 'quartz countertops',
    'gourmet kitchen', 'master suite', 'walk-in closet', 'fireplace',
    'backyard', 'patio', 'deck', 'balcony', 'solar', 'central air',
    'tennis courts', 'gated', 'cul-de-sac', 'waterfront',
}


class ListingSummarizer:
    """
    Generates 2-3 sentence summaries of MLS listing remarks for use in
    search results and email alerts. Uses an extractive approach: scores
    each sentence by entity mentions, amenity hits, and position, then
    returns the top-N in their original order so the summary reads naturally.

    Designed to consume the output of EntityExtractor.extract_all(), which
    returns a dict with keys: bedrooms, bathrooms, price, sqft, amenities.
    """

    def __init__(self, num_sentences=2, min_sentence_words=4):
        """
        Args:
            num_sentences: How many sentences the summary should contain.
            min_sentence_words: Sentences shorter than this are filtered out
                (drops headers like "Key Features:" that score artificially high).
        """
        _ensure_nltk()
        self.num_sentences = num_sentences
        self.min_sentence_words = min_sentence_words

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_present(value):
        """Treat None and NaN as missing. Everything else (including 0) is present."""
        if value is None:
            return False
        if isinstance(value, float) and math.isnan(value):
            return False
        return True

    @staticmethod
    def _mentions_number(sentence, value):
        """
        Word-boundary check for a numeric entity in a sentence.
        Avoids the bug where '3' inside '$300,000' counts as a bedroom mention.
        """
        if value is None:
            return False
        # Match the integer portion (3.0 -> "3", 2.5 stays "2.5")
        if isinstance(value, float) and value.is_integer():
            num_str = str(int(value))
        else:
            num_str = str(value)
        return re.search(rf'\b{re.escape(num_str)}\b', sentence) is not None

    def _score_sentence(self, sentence, index, entities):
        """Score a single sentence based on position + entity coverage."""
        score = 0
        lower = sentence.lower()

        # Position bonus: first sentence is usually the headline
        if index == 0:
            score += 2

        # Numeric entity mentions
        if self._is_present(entities.get('bedrooms')) and \
                self._mentions_number(sentence, entities['bedrooms']):
            # Extra weight if "bed" appears nearby — disambiguates from sqft
            if 'bed' in lower or 'br' in lower:
                score += 2
            else:
                score += 1

        if self._is_present(entities.get('bathrooms')) and \
                self._mentions_number(sentence, entities['bathrooms']):
            if 'bath' in lower or 'ba' in lower:
                score += 2
            else:
                score += 1

        if self._is_present(entities.get('sqft')) and \
                self._mentions_number(sentence, entities['sqft']):
            score += 2

        # Price mention — usually shows up as $XXX,XXX
        if self._is_present(entities.get('price')) and '$' in sentence:
            score += 2

        # Amenity hits — tiered weighting so generic filler doesn't dominate
        amenities = entities.get('amenities') or []
        for amenity in amenities:
            if not isinstance(amenity, str):
                continue
            if re.search(rf'\b{re.escape(amenity.lower())}\b', lower):
                if amenity.lower() in HIGH_VALUE_AMENITIES:
                    score += 2
                else:
                    score += 0.5  # generic amenity, small bonus

        return score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extractive_summary(self, remarks, entities, num_sentences=None):
        """
        Produce an extractive summary of `remarks` using `entities` for scoring.

        Args:
            remarks: The raw listing description (string).
            entities: Dict from EntityExtractor.extract_all().
            num_sentences: Override the default sentence count for this call.

        Returns:
            A string containing the top N sentences in original order.
            Returns "" if remarks is empty or unusable.
        """
        if not remarks or not isinstance(remarks, str):
            return ""

        n = num_sentences if num_sentences is not None else self.num_sentences

        # Normalize line breaks (your data has \r\r\n artifacts) before tokenizing
        cleaned = re.sub(r'\s+', ' ', remarks).strip()
        if not cleaned:
            return ""

        sentences = nltk.sent_tokenize(cleaned)

        # Drop very short sentences (headers, fragments) before scoring
        sentences = [s for s in sentences if len(s.split()) >= self.min_sentence_words]

        if not sentences:
            return ""

        # If the listing is already short, just return it as-is
        if len(sentences) <= n:
            return ' '.join(sentences)

        scored = [
            (self._score_sentence(s, i, entities or {}), i, s)
            for i, s in enumerate(sentences)
        ]

        # Pick top N by score, then restore original order using the index
        top = sorted(scored, key=lambda x: x[0], reverse=True)[:n]
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
        # amenities was saved as a string repr of a list — eval it back
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