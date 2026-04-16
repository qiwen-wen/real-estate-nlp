import pandas as pd
import os
import sys
import time

# 1. PATH SETUP
# We go up two levels to reach the project root from scripts/search/
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Now we can import our custom modules using the full path
from scripts.search.semantic_search import SemanticSearcher
from scripts.search.query_parser import QueryParser

def main():
    # Use the dynamic path for your cleaned listings
    csv_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_listings.csv')
    
    print("--- Starting IDX NLP Semantic Search ---")
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please run your pipeline first.")
        return
    
    # 2. LOAD DATA
    df = pd.read_csv(csv_path)
    # Target the cleaned remarks we generated in the engine
    target_col = 'cleaned_remarks' if 'cleaned_remarks' in df.columns else 'remarks'
    remarks = df[target_col].dropna().tolist()
    
    # 3. INITIALIZE SEARCHER
    searcher = SemanticSearcher()
    # This might take a second as it downloads the model weights (e.g., MiniLM)
    searcher.build_index(remarks)
    
    # 4. INITIALIZE QUERY PARSER (For structured filtering)
    parser = QueryParser()
    
    # 5. RUN A TEST QUERY
    query = "condo in upland with 3 bedrooms"
    
    # Log the filters we extracted
    filters = parser.parse(query)
    print(f"Extracted Filters: {filters}")

    start = time.time()
    # results is a list of tuples: (text, score)
    results = searcher.search(query, top_k=3)
    end = time.time()

    latency_ms = (end - start) * 1000
    print(f"\n{'='*30}")
    print(f"SEARCH LATENCY: {latency_ms:.2f}ms") 
    print(f"{'='*30}")
    
    print(f"\nTop Semantic Results for: '{query}'")
    
    # 6. OUTPUT RESULTS
    for text, score in results:
        print("-" * 20)
        # Scores closer to 1.0 are more relevant
        print(f"Similarity Score: {score:.4f}")
        print(f"Listing: {text[:150]}...")

if __name__ == "__main__":
    main()