import pandas as pd
import os
import json
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.utils.paths import CLEANED_CSV, SIGNALS_JSON, TAXONOMY_JSON, ensure_dirs
from scripts.engine.entity_extractor import EntityExtractor
from scripts.engine.signal_extractor import SignalExtractor

def run_pipeline():
    ensure_dirs()

    if not os.path.exists(CLEANED_CSV):
        print(f"Error: {CLEANED_CSV} not found.")
        print("Run convert_sql.py first to generate the cleaned CSV.")
        return

    print("Initializing Extractors...")
    week3_ext = EntityExtractor(taxonomy_path=TAXONOMY_JSON)
    signal_ext = SignalExtractor(taxonomy_path=TAXONOMY_JSON, entity_extractor=week3_ext)

    print(f"Loading {CLEANED_CSV}...")
    df = pd.read_csv(CLEANED_CSV, low_memory=False).fillna('')

    print(f"Starting extraction on {len(df)} records...")
    processed_records = []

    for index, row in df.iterrows():
        record_dict = row.to_dict()
        signals = signal_ext.extract_signals(record_dict)
        processed_records.append(signals)

        if (index + 1) % 2000 == 0:
            print(f"Progress: {index + 1}/{len(df)} records processed.")

    print(f"\nFinalizing JSON output...")
    try:
        with open(SIGNALS_JSON, 'w', encoding='utf-8') as f:
            json_string = json.dumps(processed_records, indent=4, ensure_ascii=True, default=str)
            f.write(json_string)
        print(f"SUCCESS: Saved {len(processed_records)} records to {SIGNALS_JSON}")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to write JSON: {e}")

if __name__ == "__main__":
    run_pipeline()