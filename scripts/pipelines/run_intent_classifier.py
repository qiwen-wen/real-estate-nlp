import json
import os
import sys
from datetime import date
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix
)

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.utils.paths import INTENT_JSON, ensure_dirs
from scripts.engine.intent_classifier import IntentClassifier
from scripts.engine.query_dataset import LABELED_QUERIES


def run_pipeline():
    ensure_dirs()

    # ------------------------------------------------------------------ #
    # 1. Prepare data                                                     #
    # ------------------------------------------------------------------ #
    queries = [q for q, _ in LABELED_QUERIES]
    labels  = [l for _, l in LABELED_QUERIES]

    print(f"Total labeled queries: {len(queries)}")
    for label in IntentClassifier.LABELS:
        count = labels.count(label)
        print(f"  {label}: {count}")

    # ------------------------------------------------------------------ #
    # 2. Train / test split (80/20, stratified)                          #
    # ------------------------------------------------------------------ #
    X_train, X_test, y_train, y_test = train_test_split(
        queries, labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )
    print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")

    # ------------------------------------------------------------------ #
    # 3. Train classifier                                                 #
    # ------------------------------------------------------------------ #
    clf = IntentClassifier()
    clf.train(X_train, y_train)
    print("\nClassifier trained successfully.")

    # ------------------------------------------------------------------ #
    # 4. Evaluate on test set                                             #
    # ------------------------------------------------------------------ #
    y_pred = [clf.predict(q)[0] for q in X_test]
    y_conf = [clf.predict(q)[1] for q in X_test]

    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')

    print("\n" + "=" * 50)
    print("INTENT CLASSIFIER — TEST RESULTS")
    print("=" * 50)
    print(f"Accuracy  : {accuracy:.4f}  ({accuracy*100:.1f}%)")
    print(f"F1 Macro  : {f1_macro:.4f}")
    print(f"F1 Weighted: {f1_weighted:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=IntentClassifier.LABELS))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred, labels=IntentClassifier.LABELS))
    print("=" * 50)

    if accuracy >= 0.80:
        print(f"\n✅ TARGET MET: {accuracy*100:.1f}% >= 80%")
    else:
        print(f"\n⚠️  TARGET NOT MET: {accuracy*100:.1f}% < 80% — consider adding more training data")

    # ------------------------------------------------------------------ #
    # 5. Sample predictions with confidence scores                       #
    # ------------------------------------------------------------------ #
    sample_queries = [
        "show me some houses",
        "what is the average price in San Diego",
        "3 bed 2 bath under 700k in Irvine",
        "just browsing for now",
        "how do closing costs work",
        "4 bedroom home with pool under 900k in Pasadena",
        "what neighborhoods have good schools",
        "2 bed condo near the beach",
    ]

    print("\nSample Predictions:")
    print(f"{'Query':<50} {'Intent':<15} {'Confidence'}")
    print("-" * 80)
    for q in sample_queries:
        intent, conf = clf.predict(q)
        print(f"{q:<50} {intent:<15} {conf:.2%}")

    # ------------------------------------------------------------------ #
    # 6. Save results to results/                                        #
    # ------------------------------------------------------------------ #
    results = {
        "date": str(date.today()),
        "dataset_size": len(queries),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "metrics": {
            "accuracy": round(accuracy, 4),
            "f1_macro": round(f1_macro, 4),
            "f1_weighted": round(f1_weighted, 4),
        },
        "target_met": accuracy >= 0.80,
        "per_class": {
            label: {
                "precision": round(f1_score(y_test, y_pred,
                                            labels=[label], average='macro'), 4),
            }
            for label in IntentClassifier.LABELS
        },
        "sample_predictions": [
            {"query": q, "intent": clf.predict(q)[0], "confidence": round(clf.predict(q)[1], 4)}
            for q in sample_queries
        ]
    }

    with open(INTENT_JSON, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to {INTENT_JSON}")


if __name__ == "__main__":
    run_pipeline()