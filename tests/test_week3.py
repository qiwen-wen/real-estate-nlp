import pandas as pd

def calculate_metrics(true_labels, predictions):
    tp, fp, fn = 0, 0, 0
    for gold, pred in zip(true_labels, predictions):
        # We handle 0.0 vs 0 or None to prevent math errors
        gold = float(gold) if pd.notnull(gold) else None
        pred = float(pred) if pd.notnull(pred) else None

        if pred == gold and pred is not None:
            tp += 1
        elif pred is not None and pred != gold:
            fp += 1
        elif pred is None and gold is not None:
            fn += 1
            
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1

# 1. Load the data
# If your CSV HAS a header row (e.g. the first line is "id,address,city..."):
ground_truth = pd.read_csv('data/processed/listing_sample.csv')
predictions = pd.read_csv('data/processed/extraction_results.csv')

# 2. Map the columns correctly
# Make sure these match the EXACT column names in your CSV files
# Use .strip() just in case there are hidden spaces in the CSV headers
ground_truth.columns = [c.strip() for c in ground_truth.columns]
predictions.columns = [c.strip() for c in predictions.columns]

# 3. Run Evaluation
# Double check if the column in ground_truth is 'beds' or 'bedrooms'
# Evaluate Bedrooms
b_p, b_r, b_f1 = calculate_metrics(ground_truth['beds'], predictions['bedrooms'])

# Evaluate Price (Make sure you actually calculate p_f1 here!)
p_p, p_r, p_f1 = calculate_metrics(ground_truth['price'], predictions['price'])

print(f"--- RESULTS ---")
print(f"Bedrooms F1: {b_f1:.2f}")
print(f"Price F1:    {p_f1:.2f}")