import re
import json

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

        # 3. Negation: "no pool", "without garage" (New Deliverable)
        if match := re.search(r'(?:no|without)\s+([a-zA-Z]+)', query, re.I):
            filters['exclude_amenity'] = match.group(1).strip()

        # 4. City: Improved "Non-Greedy" Regex
        # This stops capturing the city if it sees "under", "below", "no", or "without"
        city_pattern = r'in\s+((?:(?!\bunder\b|\bbelow\b|\bno\b|\bwithout\b)[a-zA-Z\s])+)'
        if match := re.search(city_pattern, query, re.I):
            filters['city'] = match.group(1).strip()
            
        return filters

    def to_sql(self, filters):
        conditions = []
        params = []
        
        if 'price_max' in filters:
            conditions.append("L_SystemPrice <= %s")
            params.append(filters['price_max'])
        
        # Fixed logic: appending params for both exact and min bedrooms
        if 'bedrooms' in filters:
            conditions.append("L_Keyword2 = %s")
            params.append(filters['bedrooms'])
        elif 'bedrooms_min' in filters:
            conditions.append("L_Keyword2 >= %s")
            params.append(filters['bedrooms_min'])
            
        if 'city' in filters:
            conditions.append("L_City = %s")
            params.append(filters['city'])

        # Added Negation SQL logic
        if 'exclude_amenity' in filters:
            conditions.append("L_AllRemarks NOT LIKE %s")
            # Use % wildcard for SQL LIKE search
            params.append(f"%{filters['exclude_amenity']}%")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM rets_property WHERE {where_clause}"
        return sql, params

class SchemaValidator:
    def __init__(self, schema_path='data/schema.json'):
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

    def validate(self, filters):
        errors = []
        # Check City
        if 'city' in filters and filters['city'] not in self.schema['valid_cities']:
            errors.append(f"City '{filters['city']}' not found in database.")
        
        # Check Realistic Price Range (from your schema.json)
        if 'price_max' in filters:
            p_min = self.schema['price_range']['min']
            p_max = self.schema['price_range']['max']
            if not (p_min <= filters['price_max'] <= p_max):
                errors.append(f"Price {filters['price_max']} is outside typical range.")
                
        return len(errors) == 0, errors