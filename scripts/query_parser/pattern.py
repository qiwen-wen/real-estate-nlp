import re

WORD_NUM = r"one|two|three|four|five|six|seven|eight|nine|ten"
NUM = rf"(?:\d+(?:\.\d+)?|{WORD_NUM})"
INT_NUM = rf"(?:\d+|{WORD_NUM})"
MONEY = r"(?:\$?\s*(?:\d[\d,]{3,}(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:k|m|mm|million|thousand)))"
CITY = r"(?:[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){0,3})"
AMENITY_PHRASE = r"(?:[a-z][a-z0-9&'/-]*(?:\s+[a-z][a-z0-9&'/-]*){0,5})"

QUERY_PATTERNS = {
    # -------- price --------
    "price_between": re.compile(
        rf"\bbetween\s+(?P<price_min>{MONEY})\s+(?:and|to)\s+(?P<price_max>{MONEY})\b", re.I
    ),
    "price_range_dash": re.compile(
        rf"\bfrom\s+(?P<price_min>{MONEY})\s*[-~]\s*(?P<price_max>{MONEY})\b|\b(?P<price_min2>{MONEY})\s*[-~]\s*(?P<price_max2>{MONEY})\b",
        re.I,
    ),
    "price_max": re.compile(
        rf"\b(?:under|below|less than|up to|at most|no more than|max(?:imum)?(?:\s+price)?(?:\s+of)?)\s+(?P<price_max>{MONEY})\b",
        re.I,
    ),
    "price_min": re.compile(
        rf"\b(?:over|above|more than|at least|min(?:imum)?(?:\s+price)?(?:\s+of)?|starting at|from)\s+(?P<price_min>{MONEY})\b",
        re.I,
    ),
    "budget_max": re.compile(
        rf"\b(?:budget|price cap|ceiling)\s*(?:is|of|:)?\s*(?P<price_max>{MONEY})\b", re.I
    ),

    # -------- bedrooms --------
    "beds_between": re.compile(
        rf"\bbetween\s+(?P<beds_min>{INT_NUM})\s+(?:and|to)\s+(?P<beds_max>{INT_NUM})\s*(?:beds?|bedrooms?|br|bd)\b",
        re.I,
    ),
    "beds_range_dash": re.compile(
        rf"\b(?P<beds_min>{INT_NUM})\s*[-~]\s*(?P<beds_max>{INT_NUM})\s*(?:beds?|bedrooms?|br|bd)\b",
        re.I,
    ),
    "beds_min": re.compile(
        rf"\b(?:at least|min(?:imum)?|>=)\s*(?P<beds_min>{INT_NUM})\s*(?:beds?|bedrooms?|br|bd)\b|\b(?P<beds_min_plus>{INT_NUM})\+\s*(?:beds?|bedrooms?|br|bd)\b",
        re.I,
    ),
    "beds_max": re.compile(
        rf"\b(?:at most|up to|max(?:imum)?|<=)\s*(?P<beds_max>{INT_NUM})\s*(?:beds?|bedrooms?|br|bd)\b",
        re.I,
    ),
    "beds_exact": re.compile(
        rf"\b(?P<beds>{INT_NUM})\s*(?:beds?|bedrooms?|br|bd)\b", re.I
    ),

    # -------- bathrooms --------
    "baths_between": re.compile(
        rf"\bbetween\s+(?P<baths_min>{NUM})\s+(?:and|to)\s+(?P<baths_max>{NUM})\s*(?:baths?|bathrooms?|ba)\b",
        re.I,
    ),
    "baths_range_dash": re.compile(
        rf"\b(?P<baths_min>{NUM})\s*[-~]\s*(?P<baths_max>{NUM})\s*(?:baths?|bathrooms?|ba)\b",
        re.I,
    ),
    "baths_min": re.compile(
        rf"\b(?:at least|min(?:imum)?|>=)\s*(?P<baths_min>{NUM})\s*(?:baths?|bathrooms?|ba)\b|\b(?P<baths_min_plus>{NUM})\+\s*(?:baths?|bathrooms?|ba)\b",
        re.I,
    ),
    "baths_max": re.compile(
        rf"\b(?:at most|up to|max(?:imum)?|<=)\s*(?P<baths_max>{NUM})\s*(?:baths?|bathrooms?|ba)\b",
        re.I,
    ),
    "baths_exact": re.compile(
        rf"\b(?P<baths>{NUM})\s*(?:baths?|bathrooms?|ba)\b", re.I
    ),

    # -------- city / location --------
    "city_in": re.compile(
        rf"\b(?:in|at|around|near)\s+(?P<city>{CITY})(?=\s+(?:with|without|under|over|below|above|between|and|or)\b|[,.!?]|$)",
        re.I,
    ),
    "city_not_in": re.compile(
        rf"\b(?:not in|outside|exclude|excluding|except)\s+(?P<city_exclude>{CITY})\b", re.I
    ),

    # -------- property type --------
    "property_type": re.compile(
        r"\b(?P<property_type>condo|condominium|townhouse|townhome|single\s*family(?:\s*home)?|duplex|triplex|penthouse|apartment|loft)\b",
        re.I,
    ),

    # -------- amenities (positive) --------
    "amenity_with": re.compile(
        rf"\bwith\s+(?P<amenities>{AMENITY_PHRASE}(?:\s*(?:,|and|or)\s*{AMENITY_PHRASE})*)\b",
        re.I,
    ),
    "amenity_has": re.compile(
        rf"\b(?:has|have|having|includes?|featuring)\s+(?P<amenities>{AMENITY_PHRASE}(?:\s*(?:,|and|or)\s*{AMENITY_PHRASE})*)\b",
        re.I,
    ),

    # -------- amenities (negation) --------
    "amenity_without": re.compile(
        rf"\bwithout\s+(?P<amenities_not>{AMENITY_PHRASE}(?:\s*(?:,|and|or)\s*{AMENITY_PHRASE})*)\b",
        re.I,
    ),
    "amenity_no": re.compile(
        rf"\bno\s+(?P<amenities_not>{AMENITY_PHRASE}(?:\s*(?:,|and|or)\s*{AMENITY_PHRASE})*)\b",
        re.I,
    ),
    "amenity_not_want": re.compile(
        rf"\b(?:not looking for|don't want|do not want|avoid)\s+(?P<amenities_not>{AMENITY_PHRASE}(?:\s*(?:,|and|or)\s*{AMENITY_PHRASE})*)\b",
        re.I,
    ),

    # -------- safety / injection pre-check --------
    "sql_injection_probe": re.compile(
        r"(?:--|/\*|\*/|;|\bunion\b|\bselect\b|\bdrop\b|\binsert\b|\bdelete\b|\bupdate\b|\bor\s+1\s*=\s*1\b)",
        re.I,
    ),
}

AMENITY_SPLIT_RE = re.compile(r"\s*(?:,|and|or|/)\s*", re.I)

SQL_INJECTION_PROBE_RE = QUERY_PATTERNS["sql_injection_probe"]
PRICE_BETWEEN_RE = QUERY_PATTERNS["price_between"]
PRICE_MAX_RE = QUERY_PATTERNS["price_max"]
PRICE_MIN_RE = QUERY_PATTERNS["price_min"]
BEDS_BETWEEN_RE = QUERY_PATTERNS["beds_between"]
BEDS_MIN_RE = QUERY_PATTERNS["beds_min"]
BEDS_MAX_RE = QUERY_PATTERNS["beds_max"]
BEDS_EXACT_RE = QUERY_PATTERNS["beds_exact"]
BATHS_BETWEEN_RE = QUERY_PATTERNS["baths_between"]
BATHS_MIN_RE = QUERY_PATTERNS["baths_min"]
BATHS_MAX_RE = QUERY_PATTERNS["baths_max"]
BATHS_EXACT_RE = QUERY_PATTERNS["baths_exact"]
CITY_NOT_IN_RE = QUERY_PATTERNS["city_not_in"]
CITY_IN_RE = QUERY_PATTERNS["city_in"]
PROPERTY_TYPE_RE = QUERY_PATTERNS["property_type"]
AMENITY_WITH_RE = QUERY_PATTERNS["amenity_with"]
AMENITY_WITHOUT_RE = QUERY_PATTERNS["amenity_without"]
