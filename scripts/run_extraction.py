import pandas as pd
import os
from entity_extractor import EntityExtractor # Updated import

# 1. Initialize
# Use a relative path that works from the project root
taxonomy_path = os.path.join('data', 'processed', 'taxonomy.json')
extractor = EntityExtractor(taxonomy_path=taxonomy_path)

# 2. Load
input_path = os.path.join('data', 'processed', 'cleaned_listings.csv')
df = pd.read_csv(input_path)

# 3. Process
print("Extracting entities... this may take a moment.")
df['extracted_data'] = df['remarks'].apply(extractor.extract_all)

# 4. Expand and Save
extracted_df = df['extracted_data'].apply(pd.Series)
results = pd.concat([df[['remarks']], extracted_df], axis=1)

output_path = os.path.join('data', 'processed', 'extraction_results.csv')
results.to_csv(output_path, index=False)

print(f"Success! Results saved to {output_path}")