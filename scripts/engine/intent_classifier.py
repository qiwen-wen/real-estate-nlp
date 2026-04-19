import os
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)


class IntentClassifier:
    """
    Classifies real estate user queries into three intent categories:
      - browsing    : casual exploration, no specific criteria
      - researching : gathering info, comparing options, asking questions
      - ready_to_buy: specific criteria with price/bed/bath filters, ready to act
    """

    LABELS = ['browsing', 'researching', 'ready_to_buy']

    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                sublinear_tf=True,
                analyzer='word',
                token_pattern=r'(?u)\b\w+\b'
            )),
            ('clf', LogisticRegression(
                max_iter=2000,
                class_weight='balanced',
                C=5.0,
                solver='lbfgs'
            ))
        ])
        self.is_trained = False
        # Store classes_ order after fitting so label lookup is always correct
        self._classes = None

    def train(self, queries: list, labels: list) -> None:
        """Fit the classifier on labeled query data."""
        self.pipeline.fit(queries, labels)
        # Capture the exact class order sklearn uses internally — never assume fixed order
        self._classes = list(self.pipeline.named_steps['clf'].classes_)
        self.is_trained = True

    def predict(self, query: str) -> tuple:
        """
        Predict intent and confidence for a single query.
        Returns (intent_label, confidence_score).
        """
        if not self.is_trained:
            raise RuntimeError("Classifier must be trained before predicting.")

        probas = self.pipeline.predict_proba([query])[0]
        # Use sklearn's own classes_ order — never hardcode index mapping
        best_idx = probas.argmax()
        intent = self._classes[best_idx]
        confidence = float(probas[best_idx])
        return intent, confidence

    def predict_batch(self, queries: list) -> list:
        """Predict intent for a list of queries."""
        if not self.is_trained:
            raise RuntimeError("Classifier must be trained before predicting.")
        results = []
        for query in queries:
            intent, confidence = self.predict(query)
            results.append({
                'query': query,
                'intent': intent,
                'confidence': round(confidence, 4)
            })
        return results