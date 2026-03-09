import nltk
import pandas as pd
from collections import Counter
from nltk.util import ngrams
import json
import os

# Load the data extracted in the previous step
df = pd.read_csv('data/processed/listing_sample.csv')

# 1. CLEANING: Extract and tokenize only alphanumeric words
all_text = ' '.join(df['remarks'].dropna().str.lower())
# Filter out punctuation tokens
tokens = [word for word in nltk.word_tokenize(all_text) if word.isalnum()]

# 2. ANALYSIS: Create and count bigrams
bigrams = list(ngrams(tokens, 2))
freq = Counter(bigrams)

# 3. MAPPING: Format for JSON
terms = []
for i, (bigram, count) in enumerate(freq.most_common(200)):
    term = ' '.join(bigram)
    terms.append({"id": i + 1, "term": term})
    # This will now show much cleaner phrases like "living room"
    print(f"{term}: {count}")

# 4. EXPORT: Ensure directory exists and save
os.makedirs('data/processed', exist_ok=True)
taxonomy = {"terms": terms}
with open("data/processed/taxonomy.json", "w") as f:
    json.dump(taxonomy, f, indent=2)
