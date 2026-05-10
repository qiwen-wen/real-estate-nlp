import pytest
from scripts.compliance.compliance_checker import ComplianceChecker

# Known violations — these MUST all flag (recall test)
KNOWN_VIOLATIONS = [
    # familial_status — error
    ("Beautiful 2BR, no children allowed.", 'familial_status'),
    ("Adults only community, quiet building.", 'familial_status'),
    ("No kids allowed in the building.", 'familial_status'),
    ("Childless tenants only, peaceful community.", 'familial_status'),
    ("No families, quiet environment.", 'familial_status'),
    ("Mature residents only, no exceptions.", 'familial_status'),
    ("Singles only, great downtown location.", 'familial_status'),
    ("Empty nesters only, serene and peaceful.", 'familial_status'),
    # familial_status — warning
    ("Perfect for singles or young professionals.", 'familial_status'),
    ("Ideal for empty nesters, low-maintenance living.", 'familial_status'),
    ("Bachelor apartment downtown, one occupant only.", 'familial_status'),
    ("Perfect for couples looking for a cozy home.", 'familial_status'),
    ("Near good school district, ideal for empty nesters.", 'familial_status'),
    ("Quiet neighborhood, perfect for young professionals.", 'familial_status'),
    ("Quiet community near university.", 'familial_status'),
    # disability — error
    ("Must be able-bodied to climb stairs.", 'disability'),
    ("No wheelchairs, 3rd floor walkup.", 'disability'),
    ("Must be able to walk to public transit.", 'disability'),
    ("No mental illness allowed.", 'disability'),
    ("No disabilities allowed, full mobility required.", 'disability'),
    ("No service animals allowed on premises.", 'disability'),
    ("Must be able to climb five flights of stairs.", 'disability'),
    ("No mental health conditions, stable tenants preferred.", 'disability'),
    # disability — warning
    ("Not suitable for elderly or disabled.", 'disability'),
    ("Walk-up only building, no elevator access.", 'disability'),
    # race_color — error
    ("Lovely home in white neighborhood.", 'race_color'),
    ("No Asians or Hispanics.", 'race_color'),
    # race_color — warning
    ("Diverse area, ethnic restaurants nearby.", 'race_color'),
    ("Traditional neighborhood with long-established values.", 'race_color'),
    ("Exclusive community, membership required.", 'race_color'),
    # religion — error
    ("Christian community, family values.", 'religion'),
    ("Jewish community, warm and welcoming.", 'religion'),
    ("No Christians or Jews allowed.", 'religion'),
    # religion — warning
    ("Walking distance to St. Mary's church.", 'religion'),
    ("Near synagogue, walkable location.", 'religion'),
    ("Church-going community, values-based living.", 'religion'),
    # national_origin — error
    ("English-speaking only please.", 'national_origin'),
    ("Americans only, no foreigners.", 'national_origin'),
    ("US citizens only, no visa holders.", 'national_origin'),
    ("No immigrants, local residents only.", 'national_origin'),
    # national_origin — warning
    ("Must speak English fluently to apply.", 'national_origin'),
    ("Native speakers preferred, professional environment.", 'national_origin'),
    # sex_gender — error
    ("Women only building.", 'sex_gender'),
    ("Men only building.", 'sex_gender'),
    ("No gay couples.", 'sex_gender'),
    ("Males only apartment building.", 'sex_gender'),
    ("Females only for safety.", 'sex_gender'),
    ("No lesbian tenants.", 'sex_gender'),
    ("No trans residents allowed.", 'sex_gender'),
]

# Known compliant listings — these MUST NOT flag at error level (precision test)
KNOWN_COMPLIANT = [
    # property descriptions
    "Beautiful 2BR apartment with hardwood floors and updated kitchen.",
    "Cozy 1BR with high ceilings and exposed brick walls.",
    "Spacious 2BR with updated bathroom and in-unit laundry.",
    "Spacious 3BR with plenty of natural light and storage.",
    "Studio apartment on the 2nd floor with lots of closet space.",
    "2BR/2BA townhome with attached garage and fenced yard.",
    "Charming historic home with original hardwood floors and fireplace.",
    "Bright and airy 1BR with large windows and balcony.",
    "Bright south-facing unit with great morning light.",
    "White oak hardwood floors and soaring 12-foot ceilings.",
    "Recently renovated, stainless steel appliances, in-unit washer/dryer.",
    "Hardwood floors, granite countertops, stainless steel appliances.",
    "Beautiful craftsman-style home with a wraparound porch.",
    "Newly built in 2022, energy-efficient windows and HVAC.",
    "Energy-efficient appliances and low utility costs.",
    # location descriptions
    "Spacious studio near downtown, walking distance to grocery stores.",
    "Walking distance to coffee shops, restaurants, and parks.",
    "Steps from public transit, 10-minute commute to downtown.",
    "Convenient location near shopping, dining, and entertainment.",
    "Near local schools and a community park, great area.",
    "Affordable rent in a desirable neighborhood with good schools.",
    "Historic district location, original details preserved.",
    # accessibility and compliance language
    "Wheelchair accessible unit on ground floor with roll-in shower.",
    "Equal housing opportunity. ADA-compliant building.",
    "Wheelchair accessible unit with wide doorways and grab bars in bathroom.",
    "ADA-accessible bathroom with roll-in shower and grab bars.",
    "Ground floor unit with wide doorways and step-free entry.",
    # building amenities
    "Pet-friendly building with on-site laundry and parking.",
    "Cat and dog friendly, no breed restrictions.",
    "Secure building with key fob entry and on-site management.",
    "Rooftop deck and gym available to all residents.",
    "Bicycle storage and EV charging stations on-site.",
    "Garage parking included, private storage unit available.",
    "Modern amenities, including a fitness center and pool.",
    "No smoking building, well-maintained common areas.",
    # landlord and leasing
    "Friendly landlord and responsive maintenance team.",
    "Responsive property management, 24-hour maintenance line.",
    "Flexible lease terms, month-to-month available after year one.",
    "Deposit equal to one month rent, income verification required.",
    "Credit and background check required for all applicants.",
    "Section 8 vouchers accepted, income-based eligibility.",
    "All applicants welcome regardless of background.",
    # community descriptions (neutral)
    "Family-friendly neighborhood with parks and good schools.",
    "Safe and quiet neighborhood, perfect for families.",
    "Affordable housing option in a vibrant community.",
    "Beautifully maintained property with a large backyard.",
    "Great for students, close to university campus and public transit.",
    "Close to public transit, ideal for commuters.",
    "Large windows with abundant natural light and open floor plan.",
    "Utilities included: water, trash, and high-speed internet.",
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