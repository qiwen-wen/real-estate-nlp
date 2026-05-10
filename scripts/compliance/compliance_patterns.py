"""
Fair Housing Act prohibited language patterns.
Organized by protected class with severity levels.

Severity definitions:
- error: Clear violation, must be fixed before publication
- warning: Likely problematic, requires human review
- info: Potentially steering language, log for audit
"""

PROHIBITED_PATTERNS = {
    'familial_status': {
        'error': [
            r'\bno children\b', r'\bno kids\b', r'\badults? only\b',
            r'\bchildless\b', r'\bno families\b', r'\bmature (?:residents?|tenants?)\b',
            r'\bempty nesters? only\b', r'\bsingles? only\b',
        ],
        'warning': [
            r'\bperfect for (?:singles?|young professionals?|couples?)\b',
            r'\bideal for empty nesters?\b', r'\bbachelor (?:pad|apartment)\b',
            r'\bfamily[- ]friendly\b',  # context-dependent
            r'\bquiet (?:building|community)\b',  # often code for no kids
        ],
        'info': [
            r'\bnear schools?\b', r'\bgood school district\b',
        ],
    },
    'disability': {
        'error': [
            r'\bno wheelchairs?\b', r'\bable[- ]bodied\b',
            r'\bmust be able to (?:walk|climb)\b', r'\bno disabilities\b',
            r'\bno mental (?:illness|health)\b', r'\bno service animals?\b',
        ],
        'warning': [
            r'\bwalk[- ]up only\b', r'\bnot suitable for (?:elderly|disabled)\b',
        ],
        'info': [
            r'\bwalking distance\b',  # usually fine, occasionally steering
        ],
    },
    'race_color': {
        'error': [
            r'\bwhite (?:neighborhood|area|community)\b',
            r'\bblack (?:neighborhood|area)\b',
            r'\bno (?:blacks?|whites?|asians?|hispanics?|latinos?)\b',
            r'\bcolored\b', r'\boriental\b',
        ],
        'warning': [
            r'\bethnic\b', r'\bdiverse (?:area|neighborhood)\b',
            r'\bexclusive (?:neighborhood|community)\b',
            r'\btraditional (?:neighborhood|values)\b',
        ],
    },
    'religion': {
        'error': [
            r'\bchristian (?:community|building|home)\b',
            r'\bjewish (?:neighborhood|community)\b',
            r'\bmuslim (?:community|building)\b',
            r'\bno (?:christians?|jews?|muslims?)\b',
        ],
        'warning': [
            r'\bnear (?:church|synagogue|mosque|temple)\b',
            r'\bwalking distance to (?:st\.|saint) \w+\b',
            r'\bchurch[- ]going\b',
        ],
    },
    'national_origin': {
        'error': [
            r'\bno (?:foreigners?|immigrants?)\b',
            r'\benglish[- ]speaking only\b',
            r'\bamericans? only\b', r'\bus citizens? only\b',
        ],
        'warning': [
            r'\bmust speak english\b', r'\bnative speakers?\b',
        ],
    },
    'sex_gender': {
        'error': [
            r'\bmen only\b', r'\bwomen only\b', r'\bmales? only\b',
            r'\bfemales? only\b', r'\bno (?:men|women|males|females)\b',
            r'\bno (?:gay|lesbian|trans)\b',
        ],
        'warning': [
            r'\bbachelor (?:pad|apartment)\b',
            r'\bmasculine\b', r'\bfeminine\b',
        ],
    },
}

# Phrases that contain trigger words but are compliant
# (HUD-required disclosures, accessibility features, equal housing statements)
ALLOWLIST_PATTERNS = [
    r'\bequal (?:housing|opportunity)\b',
    r'\bwheelchair accessible\b',
    r'\baccessible to (?:persons?|people) with disabilities\b',
    r'\bada[- ]compliant\b',
    r'\bsection 504\b',
    r'\bfair housing\b',
    r'\bhandicap accessible\b',
]

# Suggested rewrites by category (shown to agents)
SUGGESTIONS = {
    'familial_status': "Describe the property, not the ideal occupant. "
                       "Instead of 'perfect for singles,' say 'studio apartment with one bedroom.'",
    'disability': "Describe physical features factually. "
                  "Instead of 'must be able-bodied,' say '3rd floor walk-up, no elevator.'",
    'race_color': "Remove all references to racial or ethnic composition of neighborhoods.",
    'religion': "Remove references to religious institutions or communities unless "
                "describing a factually relevant landmark (and even then, use caution).",
    'national_origin': "Remove citizenship, language, or origin requirements. "
                       "These are almost always violations.",
    'sex_gender': "Remove gender-based restrictions. Exception: shared housing where "
                  "occupants share living spaces may have limited exemptions — verify with legal.",
}