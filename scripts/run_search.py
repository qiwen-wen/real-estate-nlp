import pandas as pd
from semantic_search import SemanticSearcher
import time 

def main():
    csv_path = 'data/processed/cleaned_listings.csv'
    print("--- Starting Week 5 Semantic Search ---")
    
    # Load Data
    df = pd.read_csv(csv_path)
    remarks = df['cleaned_remarks'].dropna().tolist()
    
    # Initialize Searcher
    searcher = SemanticSearcher()
    searcher.build_index(remarks)
    
    # Run a Test Query
    query = "condo in upland with 3 bedrooms"
    start = time.time()
    results = searcher.search(query, top_k=3)
    end = time.time()

    latency_ms = (end - start) * 1000
    print(f"\n{'='*30}")
    print(f"SEARCH LATENCY: {latency_ms:.2f}ms") 
    print(f"{'='*30}")
    
    print(f"\nResults for: '{query}'")
    
    # FIXED LOOP: Accessing by index because 'results' is a list of tuples
    for text, score in results:
        print("-" * 20)
        print(f"Score: {score:.4f}")
        print(f"Listing: {text[:150]}...")

if __name__ == "__main__":
    main()