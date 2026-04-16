import nltk
import pandas as pd
import json
import os
import sys
from collections import Counter
from nltk.util import ngrams
from nltk.corpus import stopwords

def build_taxonomy():
    # 1. SETUP PROJECT PATHS
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_listings.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'taxonomy.json')

    # 2. ENSURE NLTK DATA IS READY
    # Downloading to a specific project folder is a professional touch
    nltk_data_path = os.path.join(base_dir, 'data', 'models', 'nltk_data')
    os.makedirs(nltk_data_path, exist_ok=True)
    nltk.data.path.append(nltk_data_path)
    
    for resource in ['punkt', 'stopwords', 'averaged_perceptron_tagger']:
        nltk.download(resource, download_dir=nltk_data_path, quiet=True)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please run the data pipeline first.")
        return

    # 3. ANALYSIS: Parts-of-Speech (POS) Tagging
    print("Building taxonomy... Analyzing linguistic patterns.")
    df = pd.read_csv(input_path)
    target_col = 'cleaned_remarks' if 'cleaned_remarks' in df.columns else 'remarks'
    
    all_text = ' '.join(df[target_col].dropna().astype(str).str.lower())
    
    stop_words = set(stopwords.words('english'))
    extra_stop = {'home', 'house', 'property', 'welcome', 'perfect', 'located', 'offers', 'features'}
    stop_words.update(extra_stop)

    # Tokenize and filter
    tokens = [word for word in nltk.word_tokenize(all_text) if word.isalnum() and word not in stop_words]

    # Find Adjective + Noun or Noun + Noun patterns (e.g., "granite countertops")
    tagged = nltk.pos_tag(tokens)
    candidate_bigrams = list(ngrams(tagged, 2))

    valid_terms = []
    for (w1, t1), (w2, t2) in candidate_bigrams:
        # JJ = Adjective, NN/NNS = Noun (Singular/Plural)
        if t1 in ('JJ', 'NN', 'NNS') and t2 in ('NN', 'NNS'):
            valid_terms.append(f"{w1} {w2}")

    freq = Counter(valid_terms)

    # 4. EXPORT JSON
    terms = []
    # Capture the top 150 meaningful amenity phrases
    for i, (term, count) in enumerate(freq.most_common(150)):
        terms.append({"id": i + 1, "term": term})
    
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump({"terms": terms}, f, indent=2)

    print(f"Success! Taxonomy with {len(terms)} terms saved to {output_path}")

if __name__ == "__main__":
    build_taxonomy()