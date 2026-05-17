import os
import sys
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Import your TextCleaner from the engine folder for better search results
from scripts.engine.text_cleaning import TextCleaner

class BM25Searcher:
    def __init__(self):
        self.bm25 = None
        self.df = None
        self.texts = None
        self.cleaner = TextCleaner()

    def load_and_index(self, data_path=None):
        """Helper to load the CSV and build the index in one step."""
        if data_path is None:
            data_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_listings.csv')

        if not os.path.exists(data_path):
            print(f"Error: {data_path} not found.")
            return

        self.df = pd.read_csv(data_path)
        # We index the 'remarks' or 'cleaned_remarks' column
        target_col = 'cleaned_remarks' if 'cleaned_remarks' in self.df.columns else 'remarks'
        self.texts = self.df[target_col].astype(str).tolist()
        self.build_index(self.texts)
        print(f"BM25 Index successfully built with {len(self.df)} listings.")

    def build_index(self, texts):
        """Build a BM25 index directly from a list of text strings (no CSV)."""
        self.texts = [str(t) for t in texts]
        tokenized_corpus = [t.lower().split(" ") for t in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query, top_k=3):
        if self.bm25 is None:
            return "Error: Index not built. Call load_and_index() first."

        # Clean the user query using your engine's logic
        clean_query = self.cleaner.clean_text(query)
        tokenized_query = clean_query.split(" ")

        scores = self.bm25.get_scores(tokenized_query)
        # argsort descending → indices of the top-k highest-scoring docs
        top_idx = np.argsort(scores)[::-1][:top_k]

        # Prefer full row dicts when a dataframe is loaded; otherwise fall back to text
        records = self.df.to_dict('records') if self.df is not None else None
        final_results = []
        for i in top_idx:
            i = int(i)
            payload = records[i] if records is not None else {"remarks": self.texts[i]}
            final_results.append({
                'listing': payload,
                'score': round(float(scores[i]), 4),
            })
        return final_results

if __name__ == "__main__":
    searcher = BM25Searcher()
    searcher.load_and_index()
    
    test_query = "modern kitchen with granite countertops"
    print(f"\nSearching for: '{test_query}'")
    results = searcher.search(test_query)
    
    for i, res in enumerate(results):
        addr = res['listing'].get('L_Address', 'Unknown Address')
        print(f"{i+1}. {addr} (Score: {res['score']})")