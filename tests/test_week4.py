import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.query_parser import QueryParser, SchemaValidator


@pytest.fixture
def parser(tmp_path):
    schema = {
        "allowed_cities": [
            "Irvine",
            "Los Angeles",
            "San Diego",
            "New York",
            "Austin",
            "Miami",
            "Seattle",
            "Chicago",
            "Dallas",
            "Sacramento",
            "San Jose",
            "San Francisco",
            "Temecula",
        ],
        "ranges": {
            "price": {"min": 10000, "max": 200000000},
            "beds": {"min": 0, "max": 20},
            "baths": {"min": 0, "max": 20},
        },
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    return QueryParser(
        schema_path=str(schema_path),
        allowed_amenities=[
            "pool",
            "garage",
            "fireplace",
            "garden",
            "air conditioning",
            "solar",
            "gym",
            "balcony",
        ],
    )


QUERY_CASES = [
    ("3 bed under 700k in Irvine", {"beds_min": 3, "beds_max": 3, "price_max": 700000, "city": "Irvine"}, "price_max_k"),
    ("2 bed under $900000 in Austin", {"beds_min": 2, "beds_max": 2, "price_max": 900000, "city": "Austin"}, "price_max_plain"),
    ("4 bedrooms below 1.5m in Los Angeles", {"beds_min": 4, "beds_max": 4, "price_max": 1500000, "city": "Los Angeles"}, "price_max_m"),
    ("5 bedroom less than 2 million in Miami", {"beds_min": 5, "beds_max": 5, "price_max": 2000000, "city": "Miami"}, "price_max_million"),
    ("3 bed up to 850k in Seattle", {"beds_min": 3, "beds_max": 3, "price_max": 850000, "city": "Seattle"}, "price_max_up_to"),
    ("2 bed at most 750k in Chicago", {"beds_min": 2, "beds_max": 2, "price_max": 750000, "city": "Chicago"}, "price_max_at_most"),
    ("3 bed no more than 600k in Dallas", {"beds_min": 3, "beds_max": 3, "price_max": 600000, "city": "Dallas"}, "price_max_no_more"),
    ("4 bed max price of 1.2m in San Diego", {"beds_min": 4, "beds_max": 4, "price_max": 1200000, "city": "San Diego"}, "price_max_max"),
    ("3 bed over 900k in Irvine", {"beds_min": 3, "beds_max": 3, "price_min": 900000, "city": "Irvine"}, "price_min_over"),
    ("4 bed above 1m in Austin", {"beds_min": 4, "beds_max": 4, "price_min": 1000000, "city": "Austin"}, "price_min_above"),
    ("2 bed more than 700k in Seattle", {"beds_min": 2, "beds_max": 2, "price_min": 700000, "city": "Seattle"}, "price_min_more_than"),
    ("3 bed at least 800k in Chicago", {"beds_min": 3, "beds_max": 3, "price_min": 800000, "city": "Chicago"}, "price_min_at_least"),
    ("5 bed minimum price of 2m in Miami", {"beds_min": 5, "beds_max": 5, "price_min": 2000000, "city": "Miami"}, "price_min_minimum"),
    ("between 500k and 900k in Irvine", {"price_min": 500000, "price_max": 900000, "city": "Irvine"}, "price_between"),
    ("between $600000 and $1200000 in Los Angeles", {"price_min": 600000, "price_max": 1200000, "city": "Los Angeles"}, "price_between_dollar"),
    ("between 1m and 2m in San Diego", {"price_min": 1000000, "price_max": 2000000, "city": "San Diego"}, "price_between_m"),
    ("3 bed in Irvine", {"beds_min": 3, "beds_max": 3, "city": "Irvine"}, "beds_exact_digit"),
    ("three bedrooms in Austin", {"beds_min": 3, "beds_max": 3, "city": "Austin"}, "beds_exact_word"),
    ("2 br in Miami", {"beds_min": 2, "beds_max": 2, "city": "Miami"}, "beds_exact_br"),
    ("4 bd in Seattle", {"beds_min": 4, "beds_max": 4, "city": "Seattle"}, "beds_exact_bd"),
    ("at least 3 beds in Chicago", {"beds_min": 3, "city": "Chicago"}, "beds_min_phrase"),
    ("4+ bed in Dallas", {"beds_min": 4, "city": "Dallas"}, "beds_min_plus"),
    ("minimum 2 bedrooms in San Diego", {"beds_min": 2, "city": "San Diego"}, "beds_min_minimum"),
    ("at most 5 bedrooms in Los Angeles", {"beds_max": 5, "city": "Los Angeles"}, "beds_max_phrase"),
    ("up to 4 beds in Irvine", {"beds_max": 4, "city": "Irvine"}, "beds_max_up_to"),
    ("between 2 and 4 bedrooms in Austin", {"beds_min": 2, "beds_max": 4, "city": "Austin"}, "beds_between"),
    ("2 baths in Irvine", {"baths_min": 2.0, "baths_max": 2.0, "city": "Irvine"}, "baths_exact_digit"),
    ("two bathrooms in Seattle", {"baths_min": 2.0, "baths_max": 2.0, "city": "Seattle"}, "baths_exact_word"),
    ("2.5 bath in San Diego", {"baths_min": 2.5, "baths_max": 2.5, "city": "San Diego"}, "baths_exact_decimal"),
    ("at least 2 baths in Chicago", {"baths_min": 2.0, "city": "Chicago"}, "baths_min_phrase"),
    ("3+ bathrooms in Miami", {"baths_min": 3.0, "city": "Miami"}, "baths_min_plus"),
    ("at most 3 baths in Dallas", {"baths_max": 3.0, "city": "Dallas"}, "baths_max_phrase"),
    ("up to 2.5 bathrooms in Austin", {"baths_max": 2.5, "city": "Austin"}, "baths_max_up_to"),
    ("between 2 and 3 bathrooms in Los Angeles", {"baths_min": 2.0, "baths_max": 3.0, "city": "Los Angeles"}, "baths_between"),
    ("townhouse in Irvine", {"property_type": "townhouse", "city": "Irvine"}, "ptype_townhouse"),
    ("condo in Austin", {"property_type": "condo", "city": "Austin"}, "ptype_condo"),
    ("single family home in Miami", {"property_type": "single family home", "city": "Miami"}, "ptype_sfh"),
    ("duplex in Seattle", {"property_type": "duplex", "city": "Seattle"}, "ptype_duplex"),
    ("penthouse in Chicago", {"property_type": "penthouse", "city": "Chicago"}, "ptype_penthouse"),
    ("apartment in Dallas", {"property_type": "apartment", "city": "Dallas"}, "ptype_apartment"),
    ("loft in San Francisco", {"property_type": "loft", "city": "San Francisco"}, "ptype_loft"),
    ("homes near Irvine with pool", {"city": "Irvine", "amenities_include": ["pool"]}, "city_near"),
    ("homes around Los Angeles with garage", {"city": "Los Angeles", "amenities_include": ["garage"]}, "city_around"),
    ("homes at San Diego with fireplace", {"city": "San Diego", "amenities_include": ["fireplace"]}, "city_at"),
    ("between 500k and 900k not in Irvine townhouse", {"price_min": 500000, "price_max": 900000, "city_exclude": "Irvine", "property_type": "townhouse"}, "city_exclude_not_in"),
    ("homes outside Austin with pool", {"city_exclude": "Austin", "amenities_include": ["pool"]}, "city_exclude_outside"),
    ("exclude Seattle condo", {"city_exclude": "Seattle", "property_type": "condo"}, "city_exclude_exclude"),
    ("with pool in Irvine", {"amenities_include": ["pool"], "city": "Irvine"}, "amenity_with_single"),
    ("with pool and garage in Austin", {"amenities_include": ["garage", "pool"], "city": "Austin"}, "amenity_with_multi"),
    ("with gym, balcony and solar in Miami", {"amenities_include": ["balcony", "gym", "solar"], "city": "Miami"}, "amenity_with_comma"),
    ("without pool in Seattle", {"amenities_exclude": ["pool"], "city": "Seattle"}, "amenity_without_single"),
    ("without garage and fireplace in Chicago", {"amenities_exclude": ["fireplace", "garage"], "city": "Chicago"}, "amenity_without_multi"),
    ("3 bed under 700k in Irvine with pool and garage", {"beds_min": 3, "beds_max": 3, "price_max": 700000, "city": "Irvine", "amenities_include": ["garage", "pool"]}, "combined_1"),
    ("at least 4 bedrooms and 2.5 baths in Los Angeles without pool", {"beds_min": 4, "baths_min": 2.5, "baths_max": 2.5, "city": "Los Angeles", "amenities_exclude": ["pool"]}, "combined_2"),
    ("between 700k and 1.3m condo in San Diego with balcony", {"price_min": 700000, "price_max": 1300000, "property_type": "condo", "city": "San Diego", "amenities_include": ["balcony"]}, "combined_3"),
    ("3+ beds and 2+ baths in Sacramento with solar", {"beds_min": 3, "baths_min": 2.0, "city": "Sacramento", "amenities_include": ["solar"]}, "combined_4"),
]


def _assert_subset(result, expected):
    for k, v in expected.items():
        assert k in result
        assert result[k] == v


@pytest.mark.parametrize("query, expected, _tag", QUERY_CASES)
def test_parse_query_examples(parser, query, expected, _tag):
    parsed = parser.parse(query)
    _assert_subset(parsed, expected)


def test_pattern_coverage_and_accuracy(parser):
    total = len(QUERY_CASES)
    matched = 0
    tags = set()

    for query, expected, tag in QUERY_CASES:
        tags.add(tag)
        parsed = parser.parse(query)
        if all(parsed.get(k) == v for k, v in expected.items()):
            matched += 1

    accuracy = matched / total

    assert total >= 50
    assert len(tags) >= 20
    assert accuracy >= 0.90


def test_sql_generation_is_parameterized(parser):
    parsed = parser.parse("3 bed under 700k in Irvine with pool and garage")
    sql, params = parser.to_sql(parsed)

    assert "SELECT * FROM rets_property WHERE " in sql
    assert "%s" in sql
    assert sql.count("%s") == len(params)
    assert "Irvine" not in sql
    assert "700000" not in sql
    assert "pool" not in sql
    assert "garage" not in sql


@pytest.mark.parametrize(
    "query",
    [
        "3 bed in Irvine; DROP TABLE rets_property",
        "2 bath in Austin --",
        "4 bed in Miami /* test */",
        "condo in Seattle UNION SELECT password FROM users",
        "townhouse in Dallas OR 1=1",
    ],
)
def test_sql_injection_blocked(parser, query):
    with pytest.raises(ValueError, match="injection"):
        parser.parse(query)


@pytest.mark.parametrize(
    "query, err",
    [
        ("3 bed in Atlantis", "invalid city"),
        ("50 bed in Irvine", "beds out of range"),
        ("3 bed and 30 baths in Irvine", "baths out of range"),
        ("between 900k and 500k in Irvine", "price_min cannot be greater"),
        ("between 5 and 2 bedrooms in Austin", "beds_min cannot be greater"),
        ("between 3 and 1 baths in Miami", "baths_min cannot be greater"),
    ],
)
def test_schema_validation_errors(parser, query, err):
    with pytest.raises(ValueError, match=err):
        parser.parse(query)


def test_schema_validator_default_file_exists():
    validator = SchemaValidator()
    assert "price" in validator.ranges
    assert "beds" in validator.ranges
    assert "baths" in validator.ranges
    assert len(validator.allowed_cities) > 0
