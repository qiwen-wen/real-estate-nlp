import pandas as pd
from semantic_search import SemanticSearcher
from bm25_search import BM25Searcher

# Load data
df = pd.read_csv('data/processed/cleaned_listings.csv')
remarks = df['cleaned_remarks'].dropna().tolist()

# Initialize both
semantic = SemanticSearcher()
semantic.build_index(remarks)

keyword = BM25Searcher()
keyword.build_index(remarks)

# The Test Queries
# Tip: Use queries that have synonyms to see Semantic Search win!
test_queries = [
    "3 bedroom condo in upland", # Exact match (BM25 should do well)
    "affordable student housing",   # Semantic match (might use words like 'cheap' or 'university')
    "luxury home with a pool"    # Descriptor match
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")
    
    print("\n--- SEMANTIC SEARCH ---")
    for text, score in semantic.search(query, top_k=2):
        print(f"[{score:.4f}] {text[:100]}...")
        
    print("\n--- BM25 KEYWORD SEARCH ---")
    for text, score in keyword.search(query, top_k=2):
        print(f"[{score:.4f}] {text[:100]}...")