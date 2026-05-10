import pytest
from scripts.compliance.compliance_checker import ComplianceChecker

# Known violations — these MUST all flag (recall test)
KNOWN_VIOLATIONS = [
    ("Beautiful 2BR, no children allowed.", 'familial_status'),
    ("Adults only community, quiet building.", 'familial_status'),
    ("Perfect for singles or young professionals.", 'familial_status'),
    ("Must be able-bodied to climb stairs.", 'disability'),
    ("No wheelchairs, 3rd floor walkup.", 'disability'),
    ("Lovely home in white neighborhood.", 'race_color'),
    ("Diverse area, ethnic restaurants nearby.", 'race_color'),
    ("Christian community, family values.", 'religion'),
    ("Walking distance to St. Mary's church.", 'religion'),
    ("English-speaking only please.", 'national_origin'),
    ("Americans only, no foreigners.", 'national_origin'),
    ("Women only building.", 'sex_gender'),
    ("No gay couples.", 'sex_gender'),
    ("Must be able to walk to public transit.", 'disability'),
    ("Quiet neighborhood, perfect for families.", 'familial_status'),
    ("Near good school district, ideal for empty nesters.", 'familial_status'),
    # Add ~30-50 more from real cases
]

# Known compliant listings — these MUST NOT flag at error level (precision test)
KNOWN_COMPLIANT = [
    "Beautiful 2BR apartment with hardwood floors and updated kitchen.",
    "Wheelchair accessible unit on ground floor with roll-in shower.",
    "Equal housing opportunity. ADA-compliant building.",
    "Spacious studio near downtown, walking distance to grocery stores.",
    "Pet-friendly building with on-site laundry and parking.",
    "Recently renovated, stainless steel appliances, in-unit washer/dryer.",
    "Bright and airy 1BR with large windows and balcony.",
    "Family-friendly neighborhood with parks and good schools.",
    "Close to public transit, ideal for commuters.",
    "Affordable housing option in a vibrant community.",
    "Beautifully maintained property with a large backyard.",
    "Safe and quiet neighborhood, perfect for families.",
    "Modern amenities, including a fitness center and pool.",
    "Spacious 3BR with plenty of natural light and storage.",
    "Charming historic home with original hardwood floors and fireplace.",
    "Convenient location near shopping, dining, and entertainment.",
    "Energy-efficient appliances and low utility costs.",
    "Friendly landlord and responsive maintenance team.",
    "Great for students, close to university campus and public transit.",
]


class TestRecall:
    """Every known violation must be caught (target: 100%)."""

    @pytest.fixture
    def checker(self):
        return ComplianceChecker()

    def test_all_known_violations_flagged(self, checker):
        missed = []
        for text, expected_category in KNOWN_VIOLATIONS:
            result = checker.check_listing(text)
            error_categories = {v['category'] for v in result['violations']
                                if v['severity'] == 'error'}
            warning_categories = {v['category'] for v in result['violations']
                                  if v['severity'] == 'warning'}
            if expected_category not in error_categories | warning_categories:
                missed.append((text, expected_category))

        recall = 1 - (len(missed) / len(KNOWN_VIOLATIONS))
        assert recall == 1.0, f"Recall = {recall:.2%}. Missed: {missed}"


class TestPrecision:
    """Compliant listings should not produce error-level flags (target: >80%)."""

    @pytest.fixture
    def checker(self):
        return ComplianceChecker()

    def test_compliant_listings_not_flagged(self, checker):
        false_positives = []
        for text in KNOWN_COMPLIANT:
            result = checker.check_listing(text)
            if not result['compliant']:  # has at least one error
                false_positives.append((text, result['violations']))

        precision = 1 - (len(false_positives) / len(KNOWN_COMPLIANT))
        assert precision > 0.80, f"Precision = {precision:.2%}. FPs: {false_positives}"