import json
import pandas as pd
import os

def run_test():
    pred_path = 'data/processed/extracted_signals.json'
    gt_path = 'data/rets_property.csv'

    print("--- Starting Accuracy Test ---")
    
    if not os.path.exists(pred_path):
        print("Error: extracted_signals.json not found.")
        return

    # Load Predicted Data with Error Handling
    try:
        with open(pred_path, 'r', encoding='utf-8') as f:
            predicted_records = json.load(f)
            pred_map = {str(item['listing_id']): item for item in predicted_records}
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    # Load CSV (Ground Truth)
    gt_df = pd.read_csv(gt_path, low_memory=False).fillna('')
    
    struct_total = 0
    struct_correct = 0
    keyword_precision_scores = []

    # Iterate through first 500 rows for a strong statistical sample
    test_sample = gt_df.head(500)

    for _, row in test_sample.iterrows():
        l_id = str(row['L_ListingID'])
        if l_id not in pred_map: continue
            
        p = pred_map[l_id]
        
        # Test Structured Fields (Beds/Baths/Price/Sqft)
        fields = {'bedrooms': 'L_Keyword2', 'bathrooms': 'LM_Dec_3', 'price': 'L_SystemPrice', 'sqft': 'LM_Int2_3'}
        for p_key, gt_key in fields.items():
            struct_total += 1
            pred_val = p['entities'][p_key]
            # Handle float vs int comparison (e.g. 4.0 vs 4)
            try:
                gt_val = float(row[gt_key]) if row[gt_key] != '' else None
                if pred_val == gt_val or (pred_val is None and gt_val is None):
                    struct_correct += 1
            except:
                struct_total -= 1

        # Test Free Text Keyword Matching
        remarks = row['L_Remarks'].lower()
        all_found = p['amenities'] + p['condition_keywords'] + p['location_features'] + p['financing_terms']
        
        if all_found and remarks:
            hits = [kw for kw in all_found if kw.lower() in remarks]
            keyword_precision_scores.append(len(hits) / len(all_found))

    # Metrics Calculation
    struct_acc = (struct_correct / struct_total) * 100
    avg_precision = (sum(keyword_precision_scores) / len(keyword_precision_scores)) * 100 if keyword_precision_scores else 0

    print(f"RESULTS:")
    print(f"- Structured Field Accuracy: {struct_acc:.2f}% (Requirement: 90%+)")
    print(f"- Free Text Keyword Precision: {avg_precision:.2f}% (Requirement: 75%+)")
    
    if struct_acc >= 90 and avg_precision >= 75:
        print("\nOVERALL STATUS: PASSED")
    else:
        print("\nOVERALL STATUS: FAILED - Refine Extraction Logic")

if __name__ == "__main__":
    run_test()