import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import pandas as pd
from search.semantic_search import SemanticSearcher
from search.bm25_search import BM25Searcher

def run_evaluation():
    # 1. Load Data
    df = pd.read_csv('data/processed/cleaned_listings.csv')
    remarks = df['cleaned_remarks'].dropna().tolist()
    
    # 2. Initialize both searchers
    semantic = SemanticSearcher()
    semantic.build_index(remarks)
    
    keyword = BM25Searcher()
    keyword.build_index(remarks)

    # 3. Define 50 Queries
    # Tip: Mix specific (3 bed) and vague (student) queries
    test_queries = [
        "3 bedroom condo in upland", "luxury home with pool", 
        "affordable student housing", "modern kitchen with island",
        "near ucsd campus", "ocean view apartment", 
        "quiet neighborhood house", "fixer upper opportunity",
        "pet friendly rental", "large backyard for dogs",
        "studio apartment in downtown", "family home with garage",
        "condo with gym access", "house with solar panels",
        "newly renovated bathroom", "open floor plan living room",
        "close to public transportation", "spacious closet space",
        "energy efficient appliances", "historic home with character",
        "gated community with security", "high ceilings and natural light",
        "walkable to shops and restaurants", "good school district",
        "affordable housing near university", "luxury penthouse suite",
        "suburban home with pool", "downtown loft with city views",
        "family friendly neighborhood", "modern condo with amenities",
        "house with large garage", "condo near beach",
        "home with large backyard", "apartment with balcony",
        "house with fireplace", "condo with low HOA fees",
        "home with guest house", "condo with rooftop access",
        "house with finished basement", "condo in gated community",
        "home with solar panels", "condo with in-unit laundry",
        "house with large windows", "condo with community pool",
        "home with open floor plan", "condo near public transportation",
        "house with large yard", "condo with fitness center", 
        "home with modern kitchen", "condo with pet friendly policy"
    ]

    eval_data = []

    for query in test_queries:
        # Get Top 1 from Semantic
        sem_res = semantic.search(query, top_k=1)[0] # (text, score)
        
        # Get Top 1 from BM25
        bm_res = keyword.search(query, top_k=1)[0] # (text, score)
        
        eval_data.append({
            "Query": query,
            "Semantic_Result": sem_res[0],
            "Semantic_Score": sem_res[1],
            "BM25_Result": bm_res[0],
            "BM25_Score": bm_res[1],
            "Semantic_Relevant": "", # Leave empty for manual grading
            "BM25_Relevant": ""      # Leave empty for manual grading
        })

    # 4. Save to CSV for grading
    eval_df = pd.DataFrame(eval_data)
    eval_df.to_csv('data/processed/search_evaluation_results.csv', index=False)
    print("Evaluation file created: data/processed/search_evaluation_results.csv")

if __name__ == "__main__":
    run_evaluation()