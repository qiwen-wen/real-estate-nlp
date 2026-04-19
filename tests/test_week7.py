"""
test_week7.py — Intent Classifier Tests

Tests:
  1. Dataset has 200+ labeled queries
  2. All labels are valid
  3. Each class has sufficient representation
  4. Classifier achieves 80%+ accuracy on held-out test set
  5. Confidence scores are valid probabilities
  6. Predictions work for all three intent categories
  7. Batch prediction returns correct structure
"""

import sys
import os
import pytest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.engine.intent_classifier import IntentClassifier
from scripts.engine.query_dataset import LABELED_QUERIES


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture(scope="module")
def trained_classifier():
    """Train classifier once and reuse across tests."""
    queries = [q for q, _ in LABELED_QUERIES]
    labels  = [l for _, l in LABELED_QUERIES]
    clf = IntentClassifier()
    clf.train(queries, labels)
    return clf


@pytest.fixture(scope="module")
def train_test_data():
    """Return stratified 80/20 split for accuracy testing."""
    queries = [q for q, _ in LABELED_QUERIES]
    labels  = [l for _, l in LABELED_QUERIES]
    X_train, X_test, y_train, y_test = train_test_split(
        queries, labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )
    return X_train, X_test, y_train, y_test


# ------------------------------------------------------------------ #
# Dataset Tests                                                       #
# ------------------------------------------------------------------ #

def test_dataset_has_minimum_size():
    """Dataset must contain at least 200 labeled queries."""
    assert len(LABELED_QUERIES) >= 200, (
        f"Expected 200+ queries, got {len(LABELED_QUERIES)}"
    )


def test_all_labels_are_valid():
    """Every label must be one of the three valid intent categories."""
    valid_labels = set(IntentClassifier.LABELS)
    for query, label in LABELED_QUERIES:
        assert label in valid_labels, (
            f"Invalid label '{label}' for query: '{query}'"
        )


def test_each_class_has_sufficient_examples():
    """Each intent class must have at least 50 examples."""
    labels = [l for _, l in LABELED_QUERIES]
    for label in IntentClassifier.LABELS:
        count = labels.count(label)
        assert count >= 50, (
            f"Class '{label}' has only {count} examples — need at least 50"
        )


def test_no_empty_queries():
    """No query in the dataset should be empty or whitespace only."""
    for query, _ in LABELED_QUERIES:
        assert query.strip() != "", "Found empty query in dataset"


# ------------------------------------------------------------------ #
# Classifier Accuracy Tests                                           #
# ------------------------------------------------------------------ #

def test_accuracy_meets_80_percent_target(train_test_data):
    """
    Core deliverable: classifier must achieve 80%+ accuracy
    on the held-out test set.
    """
    X_train, X_test, y_train, y_test = train_test_data
    clf = IntentClassifier()
    clf.train(X_train, y_train)

    y_pred = [clf.predict(q)[0] for q in X_test]
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nTest accuracy: {accuracy:.4f} ({accuracy*100:.1f}%)")
    assert accuracy >= 0.80, (
        f"Accuracy {accuracy*100:.1f}% is below the 80% target. "
        f"Consider adding more training examples."
    )


def test_classifier_predicts_valid_labels(trained_classifier):
    """All predictions must be one of the three valid labels."""
    test_queries = [
        "3 bed 2 bath under 700k in Irvine",
        "show me some homes",
        "what are average prices in this area",
    ]
    valid_labels = set(IntentClassifier.LABELS)
    for query in test_queries:
        intent, _ = trained_classifier.predict(query)
        assert intent in valid_labels, (
            f"Prediction '{intent}' is not a valid label"
        )


# ------------------------------------------------------------------ #
# Confidence Score Tests                                              #
# ------------------------------------------------------------------ #

def test_confidence_scores_are_valid_probabilities(trained_classifier):
    """Confidence scores must be in [0, 1]."""
    test_queries = [
        "3 bed 2 bath under 700k in Irvine",
        "show me some homes",
        "what is the average price here",
        "4 bed with pool under 1 million",
    ]
    for query in test_queries:
        _, confidence = trained_classifier.predict(query)
        assert 0.0 <= confidence <= 1.0, (
            f"Confidence {confidence} out of range for query: '{query}'"
        )


def test_high_confidence_for_clear_ready_to_buy(trained_classifier):
    """Very specific queries should produce high confidence."""
    specific_query = "3 bed 2 bath under 700k in Irvine with a pool"
    _, confidence = trained_classifier.predict(specific_query)
    assert confidence >= 0.50, (
        f"Expected high confidence for specific query, got {confidence:.2%}"
    )


# ------------------------------------------------------------------ #
# Per-Intent Prediction Tests                                         #
# ------------------------------------------------------------------ #

def test_ready_to_buy_queries_classified_correctly(trained_classifier):
    """Clear ready-to-buy queries should be classified as ready_to_buy."""
    ready_queries = [
        "3 bed 2 bath under 700k in Irvine",
        "4 bedroom home with pool under 1.2 million in Pasadena",
        "2 bed condo in San Diego under 600k no HOA",
    ]
    for query in ready_queries:
        intent, conf = trained_classifier.predict(query)
        assert intent == "ready_to_buy", (
            f"Expected 'ready_to_buy' for '{query}', got '{intent}' ({conf:.2%})"
        )


def test_browsing_queries_classified_correctly(trained_classifier):
    """Clear browsing queries should be classified as browsing."""
    browsing_queries = [
        "show me some houses",
        "just browsing for now",
        "show me available listings",
    ]
    for query in browsing_queries:
        intent, conf = trained_classifier.predict(query)
        assert intent == "browsing", (
            f"Expected 'browsing' for '{query}', got '{intent}' ({conf:.2%})"
        )


def test_researching_queries_classified_correctly(trained_classifier):
    """Clear researching queries should be classified as researching."""
    researching_queries = [
        "what is the average price of a 3 bedroom home in Irvine",
        "how much do homes cost in San Diego",
        "what are typical HOA fees in this area",
    ]
    for query in researching_queries:
        intent, conf = trained_classifier.predict(query)
        assert intent == "researching", (
            f"Expected 'researching' for '{query}', got '{intent}' ({conf:.2%})"
        )


# ------------------------------------------------------------------ #
# Batch Prediction Tests                                              #
# ------------------------------------------------------------------ #

def test_batch_prediction_returns_correct_structure(trained_classifier):
    """Batch predictions must return list of dicts with correct keys."""
    queries = ["show me homes", "3 bed under 700k in Irvine"]
    results = trained_classifier.predict_batch(queries)

    assert len(results) == len(queries)
    for result in results:
        assert "query" in result
        assert "intent" in result
        assert "confidence" in result
        assert result["intent"] in IntentClassifier.LABELS
        assert 0.0 <= result["confidence"] <= 1.0


def test_batch_prediction_matches_single_prediction(trained_classifier):
    """Batch results must match individual predictions."""
    queries = ["show me homes", "3 bed 2 bath under 700k"]
    batch_results = trained_classifier.predict_batch(queries)

    for i, query in enumerate(queries):
        single_intent, single_conf = trained_classifier.predict(query)
        assert batch_results[i]["intent"] == single_intent
        assert abs(batch_results[i]["confidence"] - single_conf) < 1e-3


# ------------------------------------------------------------------ #
# Error Handling Tests                                                #
# ------------------------------------------------------------------ #

def test_untrained_classifier_raises_error():
    """Predicting without training should raise a RuntimeError."""
    clf = IntentClassifier()
    with pytest.raises(RuntimeError, match="must be trained"):
        clf.predict("show me homes")