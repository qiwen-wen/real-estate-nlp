import re
import json
import os

class QueryParser:
    def __init__(self):
        self.multipliers = {'k': 1000, 'm': 1000000}

    def _parse_number(self, value, suffix):
        num = int(value)
        return num * self.multipliers.get(suffix.lower(), 1)

    def parse(self, query):
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

        # 4. City: Non-Greedy Regex
        city_pattern = r'in\s+((?:(?!\bunder\b|\bbelow\b|\bno\b|\bwithout\b)[a-zA-Z\s])+)'
        if match := re.search(city_pattern, query, re.I):
            filters['city'] = match.group(1).strip()
            
        return filters

    def to_sql(self, filters):
        """Translates extracted filters into a SQL query format."""
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
            # Navigate from scripts/search/ up to root, then down to data/processed/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            schema_path = os.path.join(base_dir, 'data', 'processed', 'schema.json')

        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            print(f"Successfully loaded schema from {schema_path}")
        else:
            print(f"Warning: Schema file not found at {schema_path}")
            self.schema = {'valid_cities': [], 'price_range': {'min': 0, 'max': 100000000}}

    def validate(self, filters):
        errors = []
        # Check City against schema
        if 'city' in filters and filters['city'] not in self.schema.get('valid_cities', []):
            errors.append(f"City '{filters['city']}' not found in database.")
        
        # Check Realistic Price Range
        if 'price_max' in filters:
            price_cfg = self.schema.get('price_range', {})
            p_min = price_cfg.get('min', 0)
            p_max = price_cfg.get('max', 100000000)
            if not (p_min <= filters['price_max'] <= p_max):
                errors.append(f"Price {filters['price_max']} is outside typical range.")
                
        return len(errors) == 0, errors