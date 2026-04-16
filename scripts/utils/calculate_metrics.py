import pandas as pd
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.utils.paths import SEARCH_EVAL_CSV

def calculate_final_performance():
    if not os.path.exists(SEARCH_EVAL_CSV):
        print(f"❌ Error: Could not find evaluation file at: {SEARCH_EVAL_CSV}")
        return

    try:
        df = pd.read_csv(SEARCH_EVAL_CSV)
        total_queries = len(df)

        semantic_hits = pd.to_numeric(df['Semantic_Relevant'], errors='coerce').sum()
        bm25_hits = pd.to_numeric(df['BM25_Relevant'], errors='coerce').sum()

        semantic_acc = (semantic_hits / total_queries) * 100
        bm25_acc = (bm25_hits / total_queries) * 100

        print("\n" + "="*45)
        print("📊  IDX SEARCH EVALUATION: FINAL RESULTS  📊")
        print("="*45)
        print(f"Total Test Queries: {total_queries}")
        print("-" * 45)
        print(f"Semantic Search Accuracy: {semantic_acc:.1f}% ({int(semantic_hits)}/{total_queries})")
        print(f"BM25 Keyword Accuracy:   {bm25_acc:.1f}% ({int(bm25_hits)}/{total_queries})")
        print("-" * 45)

        if semantic_acc > bm25_acc:
            improvement = semantic_acc - bm25_acc
            print(f"✅ RESULT: Semantic Search provided a {improvement:.1f}%")
            print("   lift in relevance over the keyword baseline.")
        elif semantic_acc == bm25_acc:
            print("💡 RESULT: Both methods achieved identical performance.")
        else:
            print("💡 RESULT: BM25 outperformed Semantic for this test set.")
        print("="*45 + "\n")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    calculate_final_performance()