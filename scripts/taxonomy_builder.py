import nltk
import pandas as pd
from collections import Counter
from nltk.util import ngrams
from nltk.corpus import stopwords
import json
import os

# Ensure you have the necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Load the data
df = pd.read_csv('data/processed/listing_sample.csv')

# 1. CLEANING: Remove stopwords
stop_words = set(stopwords.words('english'))
# Add real estate specific "noise" words
extra_stop = {'home', 'house', 'property', 'welcome', 'perfect', 'located', 'offers', 'features'}
stop_words.update(extra_stop)

all_text = ' '.join(df['remarks'].dropna().str.lower())
tokens = [word for word in nltk.word_tokenize(all_text) if word.isalnum() and word not in stop_words]

# 2. ANALYSIS: Use POS Tagging to find "Real" Amenities
# We want phrases like (Adjective + Noun) or (Noun + Noun)
tagged = nltk.pos_tag(tokens)
bigrams = list(ngrams(tagged, 2))

# Filter: Only keep bigrams that are (JJ/NN + NN)
# JJ = Adjective, NN = Noun
valid_bigrams = []
for (w1, t1), (w2, t2) in bigrams:
    if t1 in ('JJ', 'NN', 'NNS') and t2 in ('NN', 'NNS'):
        valid_bigrams.append(f"{w1} {w2}")

freq = Counter(valid_bigrams)

# 3. MAPPING
terms = []
# Get top 150 most common "Physical" terms
for i, (term, count) in enumerate(freq.most_common(150)):
    terms.append({"id": i + 1, "term": term})
    print(f"Amenity Found: {term} ({count})")

# 4. EXPORT
os.makedirs('data/processed', exist_ok=True)
with open("data/processed/taxonomy.json", "w") as f:
    json.dump({"terms": terms}, f, indent=2)

print("\nSuccess! Cleaned taxonomy.json created.")