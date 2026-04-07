import re
from .pattern import *
from .schema_validator import SchemaValidator

class QueryParser:
    def __init__(self, allowed_cities=None, allowed_amenities=None, schema_path=None):
        self.schema_validator = SchemaValidator(schema_path=schema_path, allowed_cities=allowed_cities)
        self.allowed_amenities = {a.lower() for a in (allowed_amenities or [])}

    def _word_to_num(self, s: str):
        m = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        s = s.strip().lower()
        if s in m:
            return m[s]
        return float(s) if "." in s else int(s)

    def _parse_money(self, text: str) -> int:
        t = text.lower().replace("$", "").replace(",", "").strip()
        mult = 1
        if t.endswith("million"):
            mult, t = 1_000_000, t[:-7].strip()
        elif t.endswith("thousand"):
            mult, t = 1_000, t[:-8].strip()
        elif t.endswith("mm"):
            mult, t = 1_000_000, t[:-2].strip()
        elif t.endswith("m"):
            mult, t = 1_000_000, t[:-1].strip()
        elif t.endswith("k"):
            mult, t = 1_000, t[:-1].strip()
        return int(float(t) * mult)

    def _split_amenities(self, text: str):
        parts = [p.strip().lower() for p in AMENITY_SPLIT_RE.split(text) if p.strip()]
        cleaned = []
        for p in parts:
            p = re.sub(r"\b(?:in|near|around|at)\s+[a-z][a-z\s.'-]*$", "", p).strip()
            p = re.sub(r"^(a|an|the)\s+", "", p)
            if p:
                cleaned.append(p)
        return cleaned

    def _clean_city(self, text: str) -> str:
        stop_re = re.compile(
            r"\b(with|without|under|over|below|above|between|and|or|"
            r"condo|minium|townhouse|townhome|single\s*family|duplex|triplex|penthouse|apartment|loft)\b",
            re.I,
        )
        m = stop_re.search(text)
        if m:
            text = text[:m.start()]
        return re.sub(r"\s+", " ", text).strip(" ,.-")

    def parse(self, query: str) -> dict:
        q = query.strip()
        if SQL_INJECTION_PROBE_RE.search(q):
            raise ValueError("potential SQL injection pattern detected")

        f = {"amenities_include": [], "amenities_exclude": []}

        # price (priority: between  max and min)
        if m := PRICE_BETWEEN_RE.search(q):
            f["price_min"] = self._parse_money(m.group("price_min"))
            f["price_max"] = self._parse_money(m.group("price_max"))
        else:
            if m := PRICE_MAX_RE.search(q):
                f["price_max"] = self._parse_money(m.group("price_max"))
            if m := PRICE_MIN_RE.search(q):
                f["price_min"] = self._parse_money(m.group("price_min"))

        # beds
        if m := BEDS_BETWEEN_RE.search(q):
            f["beds_min"] = int(self._word_to_num(m.group("beds_min")))
            f["beds_max"] = int(self._word_to_num(m.group("beds_max")))
        else:
            if m := BEDS_MIN_RE.search(q):
                v = m.group("beds_min") or m.group("beds_min_plus")
                f["beds_min"] = int(self._word_to_num(v))
            if m := BEDS_MAX_RE.search(q):
                f["beds_max"] = int(self._word_to_num(m.group("beds_max")))
            if "beds_min" not in f and "beds_max" not in f and (m := BEDS_EXACT_RE.search(q)):
                v = int(self._word_to_num(m.group("beds")))
                f["beds_min"] = v
                f["beds_max"] = v

        # baths
        if m := BATHS_BETWEEN_RE.search(q):
            f["baths_min"] = float(self._word_to_num(m.group("baths_min")))
            f["baths_max"] = float(self._word_to_num(m.group("baths_max")))
        else:
            if m := BATHS_MIN_RE.search(q):
                v = m.group("baths_min") or m.group("baths_min_plus")
                f["baths_min"] = float(self._word_to_num(v))
            if m := BATHS_MAX_RE.search(q):
                f["baths_max"] = float(self._word_to_num(m.group("baths_max")))
            if "baths_min" not in f and "baths_max" not in f and (m := BATHS_EXACT_RE.search(q)):
                v = float(self._word_to_num(m.group("baths")))
                f["baths_min"] = v
                f["baths_max"] = v

        # city
        city_not_in_match = CITY_NOT_IN_RE.search(q)
        q_for_city_in = q
        if city_not_in_match:
            f["city_exclude"] = self._clean_city(city_not_in_match.group("city_exclude"))
            q_for_city_in = q.replace(city_not_in_match.group(0), " ")
        if m := CITY_IN_RE.search(q_for_city_in):
            f["city"] = self._clean_city(m.group("city"))

        # property type
        if m := PROPERTY_TYPE_RE.search(q):
            f["property_type"] = re.sub(r"\s+", " ", m.group("property_type").lower()).strip()

        # amenities include/exclude
        for m in AMENITY_WITH_RE.finditer(q):
            f["amenities_include"].extend(self._split_amenities(m.group("amenities")))
        for m in AMENITY_WITHOUT_RE.finditer(q):
            f["amenities_exclude"].extend(self._split_amenities(m.group("amenities_not")))

        f["amenities_include"] = sorted(set(f["amenities_include"]))
        f["amenities_exclude"] = sorted(set(f["amenities_exclude"]))

        if self.allowed_amenities:
            f["amenities_include"] = [a for a in f["amenities_include"] if a in self.allowed_amenities]
            f["amenities_exclude"] = [a for a in f["amenities_exclude"] if a in self.allowed_amenities]

        self.schema_validator.validate_filters(f)
        return f

    def to_sql(self, filters: dict):
        clauses = []
        params = []

        if "price_min" in filters:
            clauses.append("price >= %s")
            params.append(filters["price_min"])
        if "price_max" in filters:
            clauses.append("price <= %s")
            params.append(filters["price_max"])

        if "beds_min" in filters:
            clauses.append("beds >= %s")
            params.append(filters["beds_min"])
        if "beds_max" in filters:
            clauses.append("beds <= %s")
            params.append(filters["beds_max"])

        if "baths_min" in filters:
            clauses.append("baths >= %s")
            params.append(filters["baths_min"])
        if "baths_max" in filters:
            clauses.append("baths <= %s")
            params.append(filters["baths_max"])

        if "city" in filters:
            clauses.append("L_City = %s")
            params.append(filters["city"])
        if "city_exclude" in filters:
            clauses.append("L_City <> %s")
            params.append(filters["city_exclude"])

        if "property_type" in filters:
            clauses.append("LOWER(property_type) = %s")
            params.append(filters["property_type"])

        for a in filters.get("amenities_include", []):
            clauses.append("LOWER(remarks) LIKE %s")
            params.append(f"%{a}%")

        for a in filters.get("amenities_exclude", []):
            clauses.append("LOWER(remarks) NOT LIKE %s")
            params.append(f"%{a}%")

        where_clause = " AND ".join(clauses) if clauses else "1=1"
        sql = f"SELECT * FROM rets_property WHERE {where_clause}"
        return sql, params
    
