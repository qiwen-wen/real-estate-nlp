from rank_bm25 import BM25Okapi
import pandas as pd

class BM25Searcher:
    def __init__(self):
        self.bm25 = None
        self.listings = None

    def build_index(self, remarks_list):
        self.listings = remarks_list
        # BM25 needs the text split into words (tokenized)
        tokenized_corpus = [doc.lower().split(" ") for doc in remarks_list]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"BM25 Index built with {len(remarks_list)} listings.")

    def search(self, query, top_k=3):
        tokenized_query = query.lower().split(" ")
        # Get the top N matching remarks
        results = self.bm25.get_top_n(tokenized_query, self.listings, n=top_k)
        # Get the actual scores for those top results
        scores = self.bm25.get_scores(tokenized_query)
        
        # Format the output to match our Semantic Searcher
        # Note: BM25 scores are not 0-1, they can be any positive number
        final_results = []
        # We find the index of the result in the original list to get its score
        for res in results:
            idx = self.listings.index(res)
            final_results.append((res, scores[idx]))
        
        return final_results