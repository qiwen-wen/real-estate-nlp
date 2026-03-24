'''Build a frequency-based taxonomy from listing remarks and export it as JSON.'''

from collections import Counter
import json
import os

import nltk
from nltk.util import ngrams
import pandas as pd

# Load the data extracted in the previous step.
df = pd.read_csv('data/processed/listing_sample.csv')

# Extract and tokenize only alphanumeric words.
all_text = ' '.join(df['remarks'].dropna().str.lower())
tokens = [word for word in nltk.word_tokenize(all_text) if word.isalnum()]

# Create and count bigrams.
bigrams = list(ngrams(tokens, 2))
freq = Counter(bigrams)

# Format the top bigrams for JSON output.
terms = []
for index, (bigram, count) in enumerate(freq.most_common(200)):
    term = ' '.join(bigram)
    terms.append({'id': index + 1, 'term': term})
    print(f'{term}: {count}')

# Ensure output directory exists and save taxonomy.
os.makedirs('data/processed', exist_ok=True)
taxonomy = {'terms': terms}
with open('data/processed/taxonomy.json', 'w', encoding='utf-8') as file_obj:
    json.dump(taxonomy, file_obj, indent=2)
