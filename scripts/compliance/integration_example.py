from compliance_checker import ComplianceChecker

checker = ComplianceChecker()


def submit_listing(listing: dict) -> dict:
    """
    Listing submission pipeline with compliance gating.

    Routing logic:
    - Any error → block submission, return violations to agent
    - Only warnings → submit but route to compliance team for review
    - Only info → submit, log for audit
    - Clean → submit immediately
    """
    text = f"{listing.get('title', '')} {listing.get('description', '')}"
    result = checker.check_listing(text)

    if result['error_count'] > 0:
        return {
            'status': 'blocked',
            'reason': 'Fair Housing Act violation detected',
            'violations': result['violations'],
            'action_required': 'Agent must revise listing before resubmission.',
        }

    if result['warning_count'] > 0:
        return {
            'status': 'pending_review',
            'reason': 'Potentially problematic language flagged',
            'violations': result['violations'],
            'action_required': 'Compliance team review within 24 hours.',
        }

    return {
        'status': 'approved',
        'audit_flags': result['violations'] if result['info_count'] > 0 else [],
    }


if __name__ == '__main__':
    # Demo: three listings showing each routing path
    blocked = {
        'title': 'Quiet Building, Adults Only',
        'description': 'Perfect for young professionals. No children allowed.',
    }
    pending = {
        'title': 'Spacious 2BR',
        'description': 'Bachelor pad in family-friendly neighborhood near St. Mary\'s.',
    }
    approved = {
        'title': 'Modern 1BR Downtown',
        'description': 'Wheelchair accessible, in-unit laundry, equal housing opportunity.',
    }

    for listing in [blocked, pending, approved]:
        print(f"Listing: {listing['title']}")
        print(f"Result: {submit_listing(listing)}\n")