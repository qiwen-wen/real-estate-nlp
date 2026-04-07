from query_parser import QueryParser, SchemaValidator

parser = QueryParser()
# Note: You'll need to create a dummy data/schema.json first!
# validator = SchemaValidator() 

test_queries = [
    # --- Category 1: Basic Exact Matches (1-10) ---
    "3 bed in Irvine", "2 br in San Diego", "4 bedroom in Los Angeles",
    "1 bed in Pasadena", "5 br in Upland", "3 bedroom in San Jose",
    "2 bed in Oceanside", "4 br in Carlsbad", "1 bedroom in Menifee",
    "3 br in Riverside",

    # --- Category 2: Price "Under/Below" Shorthand (11-20) ---
    "3 bed in Irvine under 700k", "2 br in San Diego below 1m",
    "home in Los Angeles under 2m", "condo in Pasadena below 500k",
    "4 bed in Upland under 850k", "3 br in San Jose below 1.2m",
    "2 bed in Oceanside under 600k", "5 br in Carlsbad below 3m",
    "house in Menifee under 450k", "1 br in Riverside below 300k",

    # --- Category 3: Minimum "Plus" Patterns (21-30) ---
    "3+ bed in Irvine", "2+ br in San Diego", "4+ bedroom in Los Angeles",
    "1+ bed in Pasadena", "5+ br in Upland", "3+ bedroom in San Jose",
    "2+ bed in Oceanside", "4+ br in Carlsbad", "2+ bedroom in Menifee",
    "3+ br in Riverside",

    # --- Category 4: Negations "No/Without" (31-40) ---
    "3 bed in Irvine no pool", "2 br in San Diego without HOA",
    "4 bedroom in Los Angeles no carpet", "1 bed in Pasadena without stairs",
    "5 br in Upland no solar", "3 bedroom in San Jose without garage",
    "2 bed in Oceanside no basement", "4 br in Carlsbad without gate",
    "house in Menifee no mello-roos", "condo in Riverside without balcony",

    # --- Category 5: Multi-word Cities & Complexity (41-50) ---
    "3 bed in San Diego under 900k", "4 br in Los Angeles below 2.5m",
    "2+ bed in Palm Springs no pool", "3 bed in Santa Monica under 2m",
    "5 br in Beverly Hills no lawn", "2 bed in Newport Beach below 1.5m",
    "3+ br in Huntington Beach under 1.2m", "4 bed in Laguna Niguel no HOA",
    "1 bed in Costa Mesa under 600k", "3 br in Mission Viejo below 950k",

    # --- Category 6: Edge Cases & Stress Tests (51-60) ---
    "under 500k in Irvine", "3 bed below 1m", "in San Diego 4 br",
    "2 bed no pool under 700k", "5+ br below 2m without HOA",
    "in Upland 3 bed no carpet", "under 1m in Pasadena 2+ br",
    "4 bed in Irvine no pool under 1.5m", "1+ br below 400k in Riverside",
    "no garage in Los Angeles under 1m"
]



print(f"{'Query':<30} | {'SQL Query'}")
print("-" * 80)

# In scripts/run_query_tests.py
success_count = 0

for q in test_queries:
    try:
        filters = parser.parse(q)
        sql, params = parser.to_sql(filters)
        
        # Simple validation: Did we at least get a City OR a Bed OR a Price?
        if filters:
            success_count += 1
            print(f"SUCCESS | {q[:30]:<30} | {sql}")
        else:
            print(f"FAILED  | {q[:30]:<30} | No filters parsed")
            
    except Exception as e:
        print(f"ERROR   | {q[:30]:<30} | {str(e)}")

accuracy = (success_count / len(test_queries)) * 100
print(f"\nFinal Parser Accuracy: {accuracy:.2f}%")