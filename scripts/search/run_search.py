"""
run_search.py — End-to-end query pipeline demo

Shows how intent classification routes queries before SQL generation:
  browsing    → skip SQL, suggest featured listings
  researching → skip SQL, suggest informational content
  ready_to_buy→ extract filters, generate SQL
"""
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.search.query_parser import QueryParser


def run_pipeline(queries: list):
    print("Initializing query parser with intent classifier...")
    parser = QueryParser()
    print("Ready.\n")

    print("=" * 70)
    for query in queries:
        print(f"Query: \"{query}\"")
        result = parser.parse(query)

        print(f"  Intent     : {result['intent']} ({result['confidence']:.0%} confidence)")
        print(f"  SQL Ready  : {result['sql_ready']}")
        print(f"  Message    : {result['message']}")

        if result['sql_ready'] and result['filters']:
            sql, params = parser.to_sql(result['filters'])
            print(f"  Filters    : {result['filters']}")
            print(f"  SQL        : {sql}")
            print(f"  Params     : {params}")

        print("-" * 70)


if __name__ == "__main__":
    demo_queries = [
        # browsing
        "show me some houses",
        "just looking around",
        # researching
        "what is the average price in San Diego",
        "how do closing costs work",
        # ready_to_buy
        "3 bed 2 bath under 700k in Irvine",
        "4 bedroom home with pool under 900k in Pasadena",
        "2 bed condo no HOA under 600k",
    ]
    run_pipeline(demo_queries)