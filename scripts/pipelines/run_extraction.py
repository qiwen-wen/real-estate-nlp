import pandas as pd
import os
import sys

# ROOT PATH SETUP
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.utils.paths import CLEANED_CSV, EXTRACTION_CSV, TAXONOMY_JSON, ensure_dirs
from scripts.engine.entity_extractor import EntityExtractor

ensure_dirs()

extractor = EntityExtractor(taxonomy_path=TAXONOMY_JSON)

if not os.path.exists(CLEANED_CSV):
    print(f"Error: Could not find {CLEANED_CSV}")
else:
    df = pd.read_csv(CLEANED_CSV)

    target_col = 'remarks' if 'remarks' in df.columns else 'L_Remarks'
    print(f"Extracting entities from '{target_col}'... this may take a moment.")

    df['extracted_data'] = df[target_col].apply(lambda x: extractor.extract_all(str(x)))

    extracted_df = df['extracted_data'].apply(pd.Series)
    results = pd.concat([df[[target_col]], extracted_df], axis=1)

    results.to_csv(EXTRACTION_CSV, index=False)
    print(f"Success! Results saved to {EXTRACTION_CSV}")