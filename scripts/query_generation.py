import json
import random 
import os

cities = ["Seattle", "Austin", "Chicago", "Miami", "New York"]
property_types = ["condo", "townhouse", "single family home", "duplex", "penthouse"]
amenities = ["a pool", "a large backyard", "hardwood floors", "a two-car garage", "smart home features"]
budgets = ["500k", "1 million", "800,000", "750k", "1.2 million"]

queries_dataset = []

for i in range(100):
    city = random.choice(cities)
    prop = random.choice(property_types)
    queries_dataset.append({
        "query": f"I am looking for a {prop} in {city}.",
        "intent": "find_property"
    })

for i in range(100):
    budget = random.choice(budgets)
    city = random.choice(cities)
    queries_dataset.append({
        "query": f"Are there any homes under {budget} in {city}?",
        "intent": "check_budget"
    })

for i in range(100):
    amenity = random.choice(amenities)
    city = random.choice(cities)
    queries_dataset.append({
        "query": f"Are there any homes with {amenity} in {city}?",
        "intent": "find_amenities"
    })

for i in range(100):
    amenity = random.choice(amenities)
    city = random.choice(cities)
    budget = random.choice(budgets)
    queries_dataset.append({
        "query": f"Are there any homes with {amenity} in {city} under {budget}?",
        "intent": "find_amenities_with_specific_budget"
    })

for i in range(100):
    amenity = random.choice(amenities)
    city = random.choice(cities)
    budget = random.choice(budgets)
    property_type = random.choice(property_types)
    queries_dataset.append({
        "query": f"Are there any {property_type} with {amenity} in {city} under {budget}?",
        "intent": "find_property_with_amenities_and_specific_budget"
    })


os.makedirs('data/processed', exist_ok=True)
output_path = 'data/processed/user_queries.json'

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(queries_dataset, f, indent=4)