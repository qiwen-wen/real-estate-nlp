import re
from dataclasses import dataclass, asdict
from typing import Optional
from .compliance_patterns import PROHIBITED_PATTERNS, ALLOWLIST_PATTERNS, SUGGESTIONS


@dataclass
class Violation:
    category: str
    severity: str  # 'error', 'warning', 'info'
    matched_text: str
    start: int
    end: int
    message: str
    suggestion: str

    def to_dict(self):
        return asdict(self)


class ComplianceChecker:
    def __init__(self):
        # Pre-compile all patterns once at init for performance
        self.compiled_patterns = {}
        for category, severity_dict in PROHIBITED_PATTERNS.items():
            self.compiled_patterns[category] = {}
            for severity, pattern_list in severity_dict.items():
                self.compiled_patterns[category][severity] = [
                    re.compile(p, re.IGNORECASE) for p in pattern_list
                ]

        self.allowlist = [re.compile(p, re.IGNORECASE) for p in ALLOWLIST_PATTERNS]

    def _is_allowlisted(self, text: str, start: int, end: int, window: int = 40) -> bool:
        """
        Check if a match falls within an allowlisted phrase.
        Looks at a window of characters around the match.
        Example: 'wheelchair' in 'wheelchair accessible' should not flag.
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end]
        return any(pattern.search(context) for pattern in self.allowlist)

    def check_listing(self, text: str) -> dict:
        violations = []

        for category, severity_dict in self.compiled_patterns.items():
            for severity, patterns in severity_dict.items():
                for pattern in patterns:
                    for match in pattern.finditer(text):
                        # Skip if this match is in an allowlisted context
                        if self._is_allowlisted(text, match.start(), match.end()):
                            continue

                        violations.append(Violation(
                            category=category,
                            severity=severity,
                            matched_text=match.group(),
                            start=match.start(),
                            end=match.end(),
                            message=self._build_message(category, severity, match.group()),
                            suggestion=SUGGESTIONS.get(category, ""),
                        ))

        # Sort by position so the agent sees them in reading order
        violations.sort(key=lambda v: v.start)

        return {
            'compliant': not any(v.severity == 'error' for v in violations),
            'requires_review': any(v.severity == 'warning' for v in violations),
            'error_count': sum(1 for v in violations if v.severity == 'error'),
            'warning_count': sum(1 for v in violations if v.severity == 'warning'),
            'info_count': sum(1 for v in violations if v.severity == 'info'),
            'violations': [v.to_dict() for v in violations],
        }

    def _build_message(self, category: str, severity: str, matched: str) -> str:
        templates = {
            'error': f"Prohibited language ({category}): '{matched}' is a Fair Housing Act violation and must be removed.",
            'warning': f"Potentially problematic language ({category}): '{matched}' may indicate steering or exclusion. Review before publishing.",
            'info': f"Note ({category}): '{matched}' is generally permitted but flagged for audit purposes.",
        }
        return templates[severity]