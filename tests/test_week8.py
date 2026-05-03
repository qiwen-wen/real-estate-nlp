"""
Build a stratified test set for ListingSummarizer evaluation.

Samples 30 listings from extraction_results.csv across 6 strata
(rich, sparse, high-value-amenity, generic-amenity, short, long) so the
test set reflects real-world diversity rather than whatever happens to
sit at the top of the CSV.

Output: data/processed/summarizer_test_set.csv with columns
  listing_id, stratum, remarks, bedrooms, bathrooms, price, sqft, amenities,
  reference_summary, notes

Fill in `reference_summary` by hand for each row, then use the eval
script to compute ROUGE-L.
"""

import os
import ast
import random
import pandas as pd

# Match the convention used in entity_extractor.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV = os.path.join(BASE_DIR, 'results', 'extraction_results.csv')
OUTPUT_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'summarizer_test_set.csv')

# Same set used by the summarizer — keep these in sync
HIGH_VALUE_AMENITIES = {
    'pool', 'spa', 'hot tub', 'garage', 'car garage', 'view', 'ocean view',
    'mountain views', 'hardwood floors', 'granite countertops', 'quartz countertops',
    'gourmet kitchen', 'master suite', 'walk-in closet', 'fireplace',
    'backyard', 'patio', 'deck', 'balcony', 'solar', 'central air',
    'tennis courts', 'gated', 'cul-de-sac', 'waterfront',
}

PER_STRATUM = 5  # 5 * 6 strata = 30 listings
SEED = 42


def parse_amenities(value):
    """Amenities are stored as a string repr of a list — parse safely."""
    if not isinstance(value, str):
        return []
    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def count_sentences(text):
    """Rough sentence count — good enough for stratifying."""
    if not isinstance(text, str):
        return 0
    # Split on . ! ? followed by whitespace
    import re
    return len([s for s in re.split(r'[.!?]+\s+', text) if s.strip()])


def has_high_value_amenity(amenities):
    return any(a.lower() in HIGH_VALUE_AMENITIES for a in amenities)


def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(
            f"Could not find {INPUT_CSV}. Run Week 3 entity extraction first."
        )

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} listings from extraction_results.csv")

    # Pre-compute helpers
    df['_amenities_list'] = df['amenities'].apply(parse_amenities)
    df['_amenity_count'] = df['_amenities_list'].apply(len)
    df['_has_hv'] = df['_amenities_list'].apply(has_high_value_amenity)
    df['_sentence_count'] = df['remarks'].apply(count_sentences)
    df['_entity_completeness'] = (
        df['bedrooms'].notna().astype(int)
        + df['bathrooms'].notna().astype(int)
        + df['price'].notna().astype(int)
        + df['sqft'].notna().astype(int)
    )

    # Define strata — note these can overlap, that's fine, dedupe at the end
    strata = {
        'rich_entities': df[df['_entity_completeness'] >= 3],
        'sparse_entities': df[df['_entity_completeness'] <= 1],
        'high_value_amenities': df[df['_has_hv']],
        'generic_amenities_only': df[~df['_has_hv'] & (df['_amenity_count'] >= 3)],
        'short_listing': df[df['_sentence_count'] <= 4],
        'long_listing': df[df['_sentence_count'] >= 10],
    }

    print("\nStratum sizes (before sampling):")
    for name, subset in strata.items():
        print(f"  {name:30s} {len(subset)}")

    rng = random.Random(SEED)
    selected_indices = set()
    rows = []

    for stratum_name, subset in strata.items():
        # Filter out already-selected listings to avoid duplication across strata
        available = subset[~subset.index.isin(selected_indices)]
        n = min(PER_STRATUM, len(available))
        if n == 0:
            print(f"  WARNING: stratum '{stratum_name}' has no unique listings left")
            continue
        picked = available.sample(n=n, random_state=rng.randint(0, 2**32 - 1))
        for idx, row in picked.iterrows():
            selected_indices.add(idx)
            rows.append({
                'listing_id': idx,
                'stratum': stratum_name,
                'remarks': row['remarks'],
                'bedrooms': row['bedrooms'],
                'bathrooms': row['bathrooms'],
                'price': row['price'],
                'sqft': row['sqft'],
                'amenities': row['amenities'],  # original string form
                'reference_summary': '',  # YOU fill this in
                'notes': '',
            })

    out_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nWrote {len(out_df)} listings to {OUTPUT_CSV}")
    print("\nNext step: open the CSV and write a 2-3 sentence reference_summary")
    print("for each row by hand. Tips:")
    print("  - Mention bed/bath/price/sqft if available")
    print("  - Mention 1-2 standout amenities")
    print("  - Keep it natural, not a robotic list")
    print("  - This is what your model will be graded against — be honest")


if __name__ == "__main__":
    main()