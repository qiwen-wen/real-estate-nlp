"""
One-time script to build and persist the FAISS index from extraction_results.csv.
Run this once before starting the API. Re-run if listings change.

Usage:
    python -m scripts.pipelines.build_search_index
"""
import os
import sys
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.search.semantic_search import SemanticSearcher


def main():
    csv_path = os.path.join(base_dir, 'results', 'extraction_results.csv')
    index_path = os.path.join(base_dir, 'data', 'models', 'faiss_index.bin')
    listings_path = os.path.join(base_dir, 'data', 'models', 'indexed_listings.json')

    print(f"Loading listings from {csv_path}...")
    df = pd.read_csv(csv_path)
    remarks = df['remarks'].dropna().astype(str).tolist()
    print(f"Loaded {len(remarks)} listings.")

    searcher = SemanticSearcher()
    searcher.build_index(remarks)
    searcher.save_index(index_path, listings_path)
    print("Done. API can now load this index at startup.")


if __name__ == "__main__":
    main()