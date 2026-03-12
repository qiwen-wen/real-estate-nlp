import pytest
import json
import pandas as pd

def test_taxonomy_loaded():
    with open('data/processed/taxonomy.json') as f:
        tax = json.load(f)
    assert len(tax['terms']) >= 200
    assert all('id' in t and 'term' in t for t in tax['terms'])

def test_sample_data_quality():
    df = pd.read_csv('data/processed/listing_sample.csv')
    assert len(df) >= 500
    assert df['remarks'].str.len().min() > 50

def test_taxonomy_coverage():
    with open('data/processed/taxonomy.json') as f:
        tax = json.load(f)
    terms = [t['term'].lower() for t in tax['terms']]

    df = pd.read_csv('data/processed/listing_sample.csv')
    all_remarks = ' '.join(df['remarks'].dropna().astype(str).str.lower())
    
    found_terms = [term for term in terms if term in all_remarks]
    coverage = len(found_terms) / len(terms)
    
    assert coverage >= 0.30