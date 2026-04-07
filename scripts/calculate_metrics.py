import pandas as pd
import os

def calculate_final_performance():
    # Path to your graded CSV
    file_path = 'data/processed/search_evaluation_results.csv'
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Could not find {file_path}")
        print("Make sure you exported your Excel/Numbers file back to CSV format!")
        return

    try:
        # 1. Load the graded data
        df = pd.read_csv(file_path)
        total_queries = len(df)
        
        # 2. Convert 'Relevant' columns to numbers (1s and 0s)
        # errors='coerce' turns empty cells or typos into 'NaN' which .sum() ignores
        semantic_hits = pd.to_numeric(df['Semantic_Relevant'], errors='coerce').sum()
        bm25_hits = pd.to_numeric(df['BM25_Relevant'], errors='coerce').sum()
        
        # 3. Calculate Accuracy (Precision @ 1)
        semantic_acc = (semantic_hits / total_queries) * 100
        bm25_acc = (bm25_hits / total_queries) * 100
        
        # 4. Print the Professional Report for IDX
        print("\n" + "="*45)
        print("📊  IDX SEARCH EVALUATION: WEEK 5 RESULTS  📊")
        print("="*45)
        print(f"Total Test Queries: {total_queries}")
        print("-" * 45)
        print(f"Semantic Search Accuracy: {semantic_acc:.1f}% ({int(semantic_hits)}/{total_queries})")
        print(f"BM25 Keyword Accuracy:   {bm25_acc:.1f}% ({int(bm25_hits)}/{total_queries})")
        print("-" * 45)
        
        # Performance Summary
        if semantic_acc > bm25_acc:
            improvement = semantic_acc - bm25_acc
            print(f"✅ RESULT: Semantic Search provided a {improvement:.1f}%")
            print("   improvement in relevance over the baseline.")
        else:
            print("💡 RESULT: BM25 performed equal to or better than Semantic.")
        print("="*45 + "\n")

    except Exception as e:
        print(f"❌ unexpected error: {e}")

if __name__ == "__main__":
    calculate_final_performance()