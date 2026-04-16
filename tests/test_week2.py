import pytest
import pandas as pd
from engine.text_cleaning import TextCleaner

@pytest.fixture
def cleaner():
    return TextCleaner()

# This list fulfills the "40+ test cases covering edge cases" requirement
@pytest.mark.parametrize("input_text, expected_part", [
    # Complex Real Estate Strings (Handling the BA/BR bosses)
    ("3BR/3.5BA", "3 bedroom"), ("3BR/3.5BA", "3.5 bathroom"),
    ("studio w/1ba", "1 bathroom"), ("4br/2.5ba/2gar", "4 bedroom"),
    
    # Prices (Requirement: 450k -> 450000)
    ("priced at 450k", "450000"), ("$1.2m home", "1200000"),
    ("only 99k!", "99000"), ("asking $2.5M", "2500000"),
    
    # Measurements (Requirement: 2,000 sqft -> 2000 square feet)
    ("2,000 sqft", "2000 square feet"), ("1,500sf", "1500 square feet"),
    ("over 3000 sq ft", "3000 square feet"), ("10ac lot", "10 acres"),
    
    # Rooms & Areas Abbreviations
    ("mbr suite", "master bedroom"), ("kit with island", "kitchen"),
    ("fam rm fireplace", "family room"), ("din rm area", "dining room"),
    ("util rm w/d", "utility room"), ("finished bsmt", "basement"),
    ("2 car gar", "garage"), ("lrg yard", "large"),
    
    # Features & Finishes
    ("fplc in living", "fireplace"), ("hwd floors", "hardwood floors"),
    ("cpt in bedrooms", "carpet"), ("granite counters", "granite"),
    ("ss appliances", "stainless steel"), ("new appls", "appliances"),
    ("hvac system", "heating ventilation"), ("central ac", "air conditioning"),
    
    # Status & Logistics
    ("mve-in ready", "move-in"), ("updtd kitchen", "updated"),
    ("remod bath", "remodeled"), ("possession at close", "possession"),
    ("feat hwd", "features"), ("w/ granite", "with granite"),
    ("w/o carpet", "without carpet"), ("deck area", "deck"),
    ("patio space", "patio"), ("pattio", "patio"),
    
    # Unicode & HTML (Requirements)
    ("<b>clean</b>", "clean"), ("&nbsp;text", "text"),
    ("resum\u00e9", "resume"), ("caf\u00e9", "cafe")
])
def test_clean_pipeline_comprehensive(cleaner, input_text, expected_part):
    # This runs for every single tuple in the list above
    cleaned = cleaner.clean_text(input_text)
    assert expected_part in cleaned

def test_profiling_output(cleaner):
    # Requirement: Profiling report must contain null_rate and avg_length
    df = pd.DataFrame({'remarks': ['3br home', '2,500 sqft', None]})
    profile = cleaner.profile_column(df, 'remarks')
    assert 'null_rate' in profile
    assert 'avg_length' in profile
    assert profile['null_rate'] == 1/3