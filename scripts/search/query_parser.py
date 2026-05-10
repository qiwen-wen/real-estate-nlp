import re
import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.engine.intent_classifier import IntentClassifier
from scripts.engine.query_dataset import LABELED_QUERIES


def _build_trained_classifier() -> IntentClassifier:
    """Train and return a classifier using the full labeled dataset."""
    clf = IntentClassifier()
    queries = [q for q, _ in LABELED_QUERIES]
    labels  = [l for _, l in LABELED_QUERIES]
    clf.train(queries, labels)
    return clf


class QueryParser:
    """
    Parses natural language real estate queries into structured filters and SQL.

    Week 7 enhancement: integrates IntentClassifier to enrich output with
    intent and confidence before deciding whether to parse for SQL filters.

    Intent routing:
      - browsing    → return intent info only, skip SQL (no specific criteria)
      - researching → return intent info only, skip SQL (informational question)
      - ready_to_buy→ full parse + SQL generation
    """

    def __init__(self, classifier: IntentClassifier = None):
        self.multipliers = {'k': 1000, 'm': 1000000}
        # Accept an injected classifier or build one automatically
        self._clf = classifier or _build_trained_classifier()

    def _parse_number(self, value, suffix):
        num = int(value)
        return num * self.multipliers.get(suffix.lower(), 1)

    def _extract_filters(self, query: str) -> dict:
        """Extract structured filters from query text (internal use)."""
        filters = {}

        # 1. Price: "under 500k", "below $1m"
        if match := re.search(r'(?:under|below)\s+\$?(\d+)([km]?)', query, re.I):
            filters['price_max'] = self._parse_number(match.group(1), match.group(2))

        # 2. Bedrooms: "3 bed", "2+ br"
        if match := re.search(r'(\d+)(\+?)\s*(?:bed|br)', query, re.I):
            if match.group(2) == '+':
                filters['bedrooms_min'] = int(match.group(1))
            else:
                filters['bedrooms'] = int(match.group(1))

        # 3. Negation: "no pool", "without garage"
        if match := re.search(r'(?:no|without)\s+([a-zA-Z]+)', query, re.I):
            filters['exclude_amenity'] = match.group(1).strip()

        # 4. City
        city_pattern = r'in\s+((?:(?!\bunder\b|\bbelow\b|\bno\b|\bwithout\b)[a-zA-Z\s])+)'
        if match := re.search(city_pattern, query, re.I):
            filters['city'] = match.group(1).strip()

        return filters

    def parse(self, query: str) -> dict:
        """
        Parse a natural language query into a rich output dict.

        Always returns:
          - intent        : 'browsing' | 'researching' | 'ready_to_buy'
          - confidence    : float 0–1
          - filters       : dict of extracted filters (empty if not ready_to_buy)
          - sql_ready     : bool — whether SQL should be generated
          - message       : human-readable explanation of routing decision

        Example outputs:

          browsing query:
          {
            'intent': 'browsing', 'confidence': 0.94, 'sql_ready': False,
            'filters': {},
            'message': 'User is browsing — no specific criteria to filter on.'
          }

          ready_to_buy query:
          {
            'intent': 'ready_to_buy', 'confidence': 0.98, 'sql_ready': True,
            'filters': {'bedrooms': 3, 'price_max': 700000, 'city': 'Irvine'},
            'message': 'Ready to buy — filters extracted and SQL ready.'
          }
        """
        intent, confidence = self._clf.predict(query)

        if intent == 'browsing':
            return {
                'intent': intent,
                'confidence': round(confidence, 4),
                'sql_ready': False,
                'filters': {},
                'message': 'User is browsing — no specific criteria to filter on. '
                           'Consider showing featured or recently listed properties.'
            }

        if intent == 'researching':
            return {
                'intent': intent,
                'confidence': round(confidence, 4),
                'sql_ready': False,
                'filters': {},
                'message': 'User is researching — informational question detected. '
                           'Consider providing market data or FAQ content instead of listings.'
            }

        # ready_to_buy — extract filters and prepare SQL
        filters = self._extract_filters(query)
        return {
            'intent': intent,
            'confidence': round(confidence, 4),
            'sql_ready': True,
            'filters': filters,
            'message': 'Ready to buy — filters extracted and SQL ready.'
        }

    def to_sql(self, filters: dict) -> tuple:
        """Translates extracted filters into a parameterized SQL query."""
        conditions = []
        params = []

        if 'price_max' in filters:
            conditions.append("L_SystemPrice <= %s")
            params.append(filters['price_max'])

        if 'bedrooms' in filters:
            conditions.append("L_Keyword2 = %s")
            params.append(filters['bedrooms'])
        elif 'bedrooms_min' in filters:
            conditions.append("L_Keyword2 >= %s")
            params.append(filters['bedrooms_min'])

        if 'city' in filters:
            conditions.append("L_City = %s")
            params.append(filters['city'])

        if 'exclude_amenity' in filters:
            conditions.append("L_Remarks NOT LIKE %s")
            params.append(f"%{filters['exclude_amenity']}%")

        if not conditions:
            return "SELECT * FROM rets_property", []

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM rets_property WHERE {where_clause}"
        return sql, params


class SchemaValidator:
    def __init__(self, schema_path=None):
        if schema_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            schema_path = os.path.join(base_dir, 'data', 'processed', 'schema.json')

        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            print(f"Successfully loaded schema from {schema_path}")
        else:
            print(f"Warning: Schema file not found at {schema_path}")
            self.schema = {'valid_cities': [], 'price_range': {'min': 0, 'max': 100000000}}

    def validate(self, filters: dict) -> tuple:
        errors = []
        allowed_cities = self.schema.get('allowed_cities', [])
        ranges = self.schema.get('ranges', {})

        if 'city' in filters and allowed_cities and filters['city'] not in allowed_cities:
            errors.append(f"City '{filters['city']}' not found in database.")

        if 'price_max' in filters:
            price_cfg = ranges.get('price', {})
            p_min = price_cfg.get('min', 0)
            p_max = price_cfg.get('max', 100_000_000)
            if not (p_min <= filters['price_max'] <= p_max):
                errors.append(f"Price {filters['price_max']} is outside typical range.")

        for key in ('bedrooms', 'bedrooms_min'):
            if key in filters:
                bed_cfg = ranges.get('beds', {})
                b_min = bed_cfg.get('min', 0)
                b_max = bed_cfg.get('max', 20)
                if not (b_min <= filters[key] <= b_max):
                    errors.append(f"Bedroom count {filters[key]} is outside typical range.")

        return len(errors) == 0, errors