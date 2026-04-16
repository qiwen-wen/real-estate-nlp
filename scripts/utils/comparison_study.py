import pandas as pd
import os
import sys

# 1. ROOT PATH SETUP
# From scripts/utils/ to the project root
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Import our modular search classes
from scripts.search.semantic_search import SemanticSearcher
from scripts.search.bm25_search import BM25Searcher

def run_comparison():
    # 2. LOAD DATA
    csv_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_listings.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run your pipeline first!")
        return

    df = pd.read_csv(csv_path)
    # Using 'cleaned_remarks' for better NLP performance
    target_col = 'cleaned_remarks' if 'cleaned_remarks' in df.columns else 'remarks'
    remarks = df[target_col].dropna().tolist()

    # 3. INITIALIZE BOTH
    print("Initializing Semantic Search (Vector Embeddings)...")
    semantic = SemanticSearcher()
    semantic.build_index(remarks)

    print("\nInitializing BM25 Search (Keyword Frequency)...")
    keyword = BM25Searcher()
    # Note: Our updated BM25Searcher class uses load_and_index()
    # If using the base version you provided earlier, keep build_index(remarks)
    keyword.load_and_index(csv_path)

    # 4. THE TEST QUERIES
    test_queries = [
        "3 bedroom condo in upland",  # Testing exact structure
        "affordable student housing",    # Testing synonyms (cheap, university)
        "luxury home with a pool"       # Testing descriptive quality
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")
        
        print("\n--- SEMANTIC SEARCH ---")
        # semantic.search returns [(text, score), ...]
        for text, score in semantic.search(query, top_k=2):
            print(f"[{score:.4f}] {text[:120]}...")
            
        print("\n--- BM25 KEYWORD SEARCH ---")
        # keyword.search returns [{'listing': {...}, 'score': score}, ...] 
        # based on our previous update to the class
        results = keyword.search(query, top_k=2)
        for res in results:
            text = res['listing'].get(target_col, "No text found")
            score = res['score']
            print(f"[{score:.2f}] {text[:120]}...")

if __name__ == "__main__":
    run_comparison()