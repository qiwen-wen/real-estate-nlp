# Fair Housing Act Compliance Guide

## What Is the FHA and Why Does It Matter

The Fair Housing Act (42 U.S.C. §§ 3601–3619), enacted in 1968 and strengthened by the Fair Housing Amendments Act of 1988, prohibits discrimination in the sale, rental, and financing of housing. It applies to virtually all residential housing, including apartment listings, online rental ads, MLS descriptions, and direct communications with prospective tenants.

**Why it matters for listing copy:**

- HUD and state agencies actively monitor listing language, including algorithmic scanning of online platforms.
- Violations carry civil penalties up to $21,663 for a first offense and $107,315 for repeated violations (amounts adjust periodically).
- Private plaintiffs can sue for actual damages, punitive damages, and attorney fees.
- Platforms (Zillow, Apartments.com, MLS systems) may remove non-compliant listings without notice.

The standard is intent-neutral: a listing can violate the FHA even if the author had no discriminatory intent. The test is whether the language would discourage a protected class from applying.

---

## The Seven Protected Classes

### 1. Race and Color

Prohibits expressing any preference for or against tenants based on race or skin color, and prohibits describing a neighborhood in racial terms (a practice called **steering**).

| Non-compliant | Compliant alternative |
|---|---|
| "Lovely home in a white neighborhood." | "Quiet residential street near Elmwood Park." |
| "Diverse area with ethnic restaurants nearby." | "Vibrant neighborhood with restaurants from around the world." |
| "No Blacks/Asians/Hispanics." | *(Any exclusion by race — no compliant rewrite exists; remove entirely.)* |

**Steering** is a subtler violation: describing a neighborhood's racial composition to guide certain applicants toward or away from it is prohibited even without explicit exclusion.

---

### 2. Color

Color is enumerated separately from race because discrimination can occur within a racial group based on skin tone. In practice, the same language rules apply as for race.

---

### 3. National Origin

Prohibits requiring specific nationalities, citizenship, or languages as a proxy for national origin.

| Non-compliant | Compliant alternative |
|---|---|
| "Americans only, no foreigners." | *(No compliant rewrite — remove entirely.)* |
| "English-speaking only please." | "Responsive communication required." *(or omit entirely)* |
| "Must be a US citizen." | *(Citizenship requirements are generally prohibited; consult legal.)* |

**Note:** Lease documents may require a government-issued ID for identity verification, but the listing itself cannot filter by national origin or citizenship.

---

### 4. Religion

Prohibits expressing a preference for tenants of a particular faith and prohibits describing a property or neighborhood in terms of its religious character in a way that steers applicants.

| Non-compliant | Compliant alternative |
|---|---|
| "Christian community, family values." | "Quiet neighborhood with active community association." |
| "Walking distance to St. Mary's Church." | "Walking distance to several local landmarks." *(or name a secular landmark instead)* |
| "No Muslims." | *(No compliant rewrite — remove entirely.)* |

**Proximity statements** are a gray area. Mentioning a place of worship as a proximity landmark can be seen as steering. The checker flags these at `warning` level for human review rather than automatic rejection.

---

### 5. Sex and Gender

Prohibits restricting housing to one sex, and under HUD's 2012 guidance, extends to sexual orientation and gender identity (LGBTQ+ protections), though some states have codified this more explicitly than federal law.

| Non-compliant | Compliant alternative |
|---|---|
| "Women only building." | *(No compliant rewrite — shared-facilities exception is narrow; consult legal.)* |
| "No gay couples." | *(No compliant rewrite — remove entirely.)* |
| "Bachelor pad, perfect for guys." | "Studio apartment, open floor plan." |

**Shared housing exception:** The FHA has a limited exemption for owner-occupied buildings with four or fewer units and for single-family homes sold/rented without a broker. Even within this exception, explicit exclusions remain high-risk and should be reviewed by legal.

---

### 6. Familial Status

Protects families with children under 18, including pregnant women and anyone in the process of securing legal custody of a child. This is one of the most commonly violated categories in listing copy.

| Non-compliant | Compliant alternative |
|---|---|
| "No children allowed." | *(No compliant rewrite — remove entirely.)* |
| "Adults only community, quiet building." | "Well-maintained building with attentive management." |
| "Perfect for singles or young professionals." | "Efficient layout, close to downtown and transit." |
| "Mature residents only." | *(No compliant rewrite — remove entirely.)* |

**55+ housing exemption:** Communities that qualify under the Housing for Older Persons Act (HOPA) may restrict occupancy to residents 55 and older, but must meet strict certification requirements. Do not use `adults only` or `55+` language without verified HOPA status.

---

### 7. Disability

Prohibits refusing to rent to persons with physical or mental disabilities, and requires reasonable accommodations and modifications. Listing language that implies physical ability requirements or discourages applicants with disabilities is a violation.

| Non-compliant | Compliant alternative |
|---|---|
| "Must be able-bodied to climb stairs." | "3rd floor walk-up, no elevator." |
| "No wheelchairs." | *(No compliant rewrite — remove entirely.)* |
| "Not suitable for the disabled." | *(No compliant rewrite — remove entirely.)* |
| "No service animals." | *(Always prohibited — service animals are not pets; no-pet policies do not apply.)* |

Describing physical features factually (no elevator, steep stairs, narrow doorways) is compliant. Restricting *who* may live there based on ability is not.

---

## Severity Levels and Workflow Actions

The checker assigns one of three severity levels to each flagged match. These map directly to what happens next in the publishing pipeline.

### `error` — Block publication

Clear, unambiguous violation of the FHA. The listing **must not be published** until the flagged language is removed or rewritten.

- Automated action: listing is held from publication and routed to the compliance queue.
- Human action required: rewrite using the suggested language or remove the phrase entirely.
- Examples: "no children," "women only," "English-speaking only," "able-bodied."

### `warning` — Hold for human review

Language that is likely problematic or context-dependent. A human reviewer must decide whether it constitutes a violation before the listing is published.

- Automated action: listing is flagged in the review queue but not hard-blocked.
- Human action required: reviewer reads the full listing in context and either approves (with a note), rewrites, or escalates.
- Examples: "quiet community" (often code for no children), "diverse area" (steering risk), proximity to a religious landmark.

### `info` — Log for audit

Language that is generally acceptable but warrants a record for audit and pattern-analysis purposes. The listing may proceed without human intervention.

- Automated action: flag is written to the audit log; no queue action.
- Human action: none required in real time; reviewed in periodic audits.
- Examples: "near schools," "good school district" (neutral, but logged to detect patterns if combined with other language).

### Workflow summary

```
Listing submitted
      │
      ▼
ComplianceChecker.check_listing()
      │
      ├─ error present? ──YES──► Hold listing, route to compliance queue
      │
      ├─ warning present? ─YES──► Route to human review queue
      │                            └─ Reviewer approves / rewrites / escalates
      │
      └─ info only (or clean) ──► Publish; write audit log entry
```

---

## Adding New Patterns When HUD Updates Guidance

HUD periodically issues guidance letters, FHEO notices, and settlement agreements that clarify what language is prohibited. When that happens, update `compliance_patterns.py` following these steps.

### Step 1: Identify the protected class and severity

Locate the relevant class in `PROHIBITED_PATTERNS` (or add a new top-level key if HUD has extended protections to a new class). Decide on severity:

- `error` if the guidance says the language is a clear violation.
- `warning` if the guidance says it is likely problematic or context-dependent.
- `info` if the guidance recommends logging it without blocking.

### Step 2: Write the regex pattern

Patterns use Python `re` syntax and are compiled with `re.IGNORECASE`. Follow these conventions:

- Use `\b` word boundaries to avoid partial matches (`\bno kids\b` won't match "no kidnapping").
- Use `(?:...)` non-capturing groups for alternatives: `\bno (?:children|kids)\b`.
- Use `?` for optional characters: `\badults? only\b` matches both "adult only" and "adults only".
- Use `[- ]` for optional hyphens/spaces: `\bable[- ]bodied\b`.
- Keep each pattern focused on one phrase. Prefer multiple simple patterns over one complex one.

```python
# Good — readable, testable individually
r'\bno children\b',
r'\bno kids\b',

# Avoid — hard to test which branch fired
r'\bno (?:children|kids|families|minors|offspring)\b',
```

### Step 3: Add an allowlist entry if needed

If the new pattern might match compliant language (e.g., a disclosure statement or accessibility feature), add a corresponding entry to `ALLOWLIST_PATTERNS`. The allowlist check uses a ±40 character window around the match, so the allowlist pattern only needs to match the immediate phrase, not the full listing.

```python
ALLOWLIST_PATTERNS = [
    ...
    r'\bnew allowlist phrase\b',  # prevents false positive on "X Y Z"
]
```

### Step 4: Update `SUGGESTIONS`

Add or update the suggestion string for the affected category. Suggestions are surfaced to the agent and human reviewer, so they should be actionable:

```python
SUGGESTIONS = {
    'new_category': "Describe the property feature factually. "
                    "Instead of '[prohibited phrase],' say '[neutral alternative].'",
}
```

### Step 5: Add test cases

Add at least one new entry to each of the test arrays in `tests/test_week9.py`:

- Add the new violating phrase to `KNOWN_VIOLATIONS` with the expected category.
- If a corresponding compliant rewrite exists, add it to `KNOWN_COMPLIANT`.

Run the test suite before committing:

```bash
python -m pytest tests/test_week9.py -v
```

### Step 6: Record the source

Add a comment above the new pattern citing the HUD guidance document and date so future maintainers know why it exists:

```python
# HUD FHEO Notice 2024-01 (Jan 2024): "exclusive neighborhood" flagged as steering
r'\bexclusive (?:neighborhood|community)\b',
```

---

## Quick Reference: Words and Phrases to Avoid

The following are high-signal terms that frequently appear in violations. This list is not exhaustive — always run listings through the checker.

| Term | Protected class | Notes |
|---|---|---|
| "no children / no kids" | Familial status | Always error |
| "adults only / mature residents" | Familial status | Always error |
| "able-bodied / must be ambulatory" | Disability | Always error |
| "no service animals" | Disability | Always error — service animals are not pets |
| "English-speaking only" | National origin | Always error |
| "no foreigners / Americans only" | National origin | Always error |
| "women only / men only" | Sex | Always error |
| "no gay / no lesbian / no trans" | Sex | Always error |
| "Christian / Jewish / Muslim community" | Religion | Error |
| "white / black neighborhood" | Race | Error |
| "quiet community" | Familial status | Warning — often code for "no children" |
| "perfect for singles / young professionals" | Familial status | Warning — implies no families |
| "diverse area / ethnic restaurants" | Race | Warning — steering risk |
| "near [named church / mosque / temple]" | Religion | Warning — can indicate steering |
| "bachelor pad" | Sex / Familial status | Warning |

---

## Additional Resources

- HUD Fair Housing page: hud.gov/fairhousing
- File a complaint: hud.gov/program_offices/fair_housing_equal_opp/online-complaint
- HUD guidance letters and FHEO notices: hud.gov/offices/fheo
- NAR Fair Housing resources: nar.realtor/fair-housing
