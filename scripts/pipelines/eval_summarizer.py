"""
Evaluate ListingSummarizer with ROUGE-L on the hand-labeled test set.

Reads:  data/processed/summarizer_test_set.csv
Writes: results/week8_summarizer_metrics.json
        results/week8_summarizer_predictions.csv

Pass criterion: mean ROUGE-L F1 > 0.4 across all labeled rows.

Run from repo root:
    python scripts/pipelines/eval_summarizer.py
"""

import os
import ast
import json
import sys

import pandas as pd
from rouge_score import rouge_scorer

# Repo path conventions match entity_extractor.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_SET_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'summarizer_test_set.csv')
METRICS_JSON = os.path.join(BASE_DIR, 'results', 'week8_summarizer_metrics.json')
PREDICTIONS_CSV = os.path.join(BASE_DIR, 'results', 'week8_summarizer_predictions.csv')

# Make scripts/engine importable when running this file directly
sys.path.insert(0, BASE_DIR)
from scripts.engine.listing_summarizer import ListingSummarizer

PASS_THRESHOLD = 0.4


def parse_amenities(value):
    """Amenities are stored as the string repr of a list — parse safely."""
    if not isinstance(value, str):
        return []
    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def main():
    if not os.path.exists(TEST_SET_CSV):
        raise FileNotFoundError(
            f"Could not find {TEST_SET_CSV}. Run build_test_set.py first."
        )

    df = pd.read_csv(TEST_SET_CSV)
    print(f"Loaded {len(df)} rows from test set")

    # Drop rows missing a reference summary (unusable listings, etc.)
    before = len(df)
    df = df[df['reference_summary'].notna() & (df['reference_summary'].str.strip() != '')]
    skipped = before - len(df)
    if skipped:
        print(f"Skipping {skipped} rows with no reference_summary")
    print(f"Evaluating on {len(df)} rows\n")

    if len(df) == 0:
        raise ValueError("No labeled rows to evaluate. Fill in reference_summary first.")

    summarizer = ListingSummarizer(num_sentences=3)
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

    rows = []
    for _, row in df.iterrows():
        entities = {
            'bedrooms': row['bedrooms'],
            'bathrooms': row['bathrooms'],
            'price': row['price'],
            'sqft': row['sqft'],
            'amenities': parse_amenities(row['amenities']),
        }
        prediction = summarizer.extractive_summary(row['remarks'], entities)
        reference = row['reference_summary']

        score = scorer.score(reference, prediction)['rougeL']
        rows.append({
            'listing_id': row['listing_id'],
            'stratum': row['stratum'],
            'reference': reference,
            'prediction': prediction,
            'rougeL_precision': round(score.precision, 4),
            'rougeL_recall': round(score.recall, 4),
            'rougeL_f1': round(score.fmeasure, 4),
        })

    results_df = pd.DataFrame(rows)

    # Overall metrics
    mean_f1 = results_df['rougeL_f1'].mean()
    median_f1 = results_df['rougeL_f1'].median()
    min_f1 = results_df['rougeL_f1'].min()
    max_f1 = results_df['rougeL_f1'].max()
    passed = mean_f1 > PASS_THRESHOLD

    # Per-stratum breakdown
    by_stratum = results_df.groupby('stratum')['rougeL_f1'].agg(['mean', 'count']).round(4)

    # Print report
    print("=" * 70)
    print("ROUGE-L EVALUATION RESULTS")
    print("=" * 70)
    print(f"Mean F1:    {mean_f1:.4f}  (target > {PASS_THRESHOLD})")
    print(f"Median F1:  {median_f1:.4f}")
    print(f"Min / Max:  {min_f1:.4f} / {max_f1:.4f}")
    print(f"Status:     {'PASS' if passed else 'FAIL'}")
    print()
    print("Per-stratum mean F1:")
    print(by_stratum.to_string())
    print()

    # Show worst 3 rows so it's clear where to debug if failing
    worst = results_df.nsmallest(3, 'rougeL_f1')
    print("3 lowest-scoring rows (debug targets):")
    for _, r in worst.iterrows():
        print(f"  listing {r['listing_id']} ({r['stratum']}) | F1={r['rougeL_f1']}")
        print(f"    REF:  {r['reference'][:120]}...")
        print(f"    PRED: {r['prediction'][:120]}...")
        print()

    # Save artifacts
    os.makedirs(os.path.dirname(METRICS_JSON), exist_ok=True)
    metrics = {
        'mean_rougeL_f1': round(mean_f1, 4),
        'median_rougeL_f1': round(median_f1, 4),
        'min_rougeL_f1': round(min_f1, 4),
        'max_rougeL_f1': round(max_f1, 4),
        'pass_threshold': PASS_THRESHOLD,
        'passed': bool(passed),
        'n_evaluated': len(results_df),
        'n_skipped': int(skipped),
        'per_stratum': {k: {'mean_f1': float(v['mean']), 'n': int(v['count'])}
                        for k, v in by_stratum.to_dict('index').items()},
    }
    with open(METRICS_JSON, 'w') as f:
        json.dump(metrics, f, indent=2)
    results_df.to_csv(PREDICTIONS_CSV, index=False)

    print(f"Saved metrics    -> {METRICS_JSON}")
    print(f"Saved predictions -> {PREDICTIONS_CSV}")


if __name__ == "__main__":
    main()