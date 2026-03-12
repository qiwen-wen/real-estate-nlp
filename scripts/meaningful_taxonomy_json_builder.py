import json
import os

taxonomy_data = {
    "Room Types": [
        "living room", "primary suite", "laundry room", "family room", "dining room", 
        "great room", "home office", "primary bedroom", "full bathroom", "guest bedroom",
        "bonus room", "mudroom", "sunroom", "powder room", "basement", "attic", "loft",
        "foyer", "entryway", "master bathroom", "media room", "playroom", "rec room",
        "utility room", "formal dining", "breakfast nook", "study", "wine cellar", "library", "guest house"
    ],
    "Interior Features": [
        "natural light", "floor plan", "vaulted ceilings", "open floor", "recessed lighting",
        "soaking tub", "walk-in closet", "smart home", "central air", "fireplace", 
        "crown molding", "french doors", "skylights", "ceiling fan", "window treatments",
        "custom built-ins", "wainscoting", "dual vanities", "high ceilings", "spacious living",
        "open concept", "security system", "tankless water heater", "energy efficient"
    ],
    "Kitchen & Appliances": [
        "stainless steel", "steel appliances", "kitchen island", "gas range", "double oven",
        "walk-in pantry", "custom cabinetry", "wine fridge", "breakfast bar", "dishwasher",
        "refrigerator", "microwave", "garbage disposal", "range hood", "farmhouse sink",
        "pot filler", "eat-in kitchen", "chef's kitchen", "smart refrigerator", "induction cooktop",
        "butler pantry", "soft close drawers", "under cabinet lighting"
    ],
    "Materials & Finishes": [
        "granite countertops", "quartz countertops", "hardwood floors", "luxury vinyl", 
        "ceramic tile", "marble floors", "carpet", "subway tile", "brick exterior", 
        "stucco", "hardie board", "exposed brick", "wood beams", "engineered hardwood",
        "slate tile", "travertine", "butcher block", "concrete floors", "shiplap", 
        "laminate flooring", "glass backsplash", "brass hardware", "matte black fixtures"
    ],
    "Exterior & Outdoor": [
        "covered patio", "pool and", "attached garage", "fenced backyard", "front porch",
        "outdoor kitchen", "fire pit", "deck", "sprinkler system", "landscaped",
        "rv parking", "storage shed", "pergola", "balcony", "cul-de-sac", "corner lot",
        "mature trees", "paver driveway", "swimming pool", "hot tub", "screened porch",
        "garden", "water feature", "outdoor fireplace", "gazebo", "wrap-around porch", "greenhouse"
    ],
    "Location & Views": [
        "mountain views", "shopping dining", "easy access", "close to", "minutes from",
        "conveniently located", "ocean view", "lakefront", "city views", "wooded lot",
        "waterfront", "park access", "highway access", "downtown", "quiet neighborhood",
        "scenic views", "walking distance", "near schools", "golf course view", "private greenbelt",
        "hill country views", "panoramic views", "river access"
    ],
    "Property Types": [
        "single family", "townhouse", "condo", "duplex", "multi family", "new construction",
        "ranch style", "two story", "split level", "historic home", "farmhouse", 
        "contemporary", "mid-century modern", "victorian", "colonial", "craftsman", 
        "penthouse", "studio", "triplex", "fourplex", "manufactured home", "cabin",
        "cottage", "estate", "investment property", "turnkey"
    ],
    "Amenities & Community": [
        "clubhouse", "fitness center", "gated community", "tennis courts", "community pool",
        "walking trails", "playground", "hoa", "guard gated", "golf course", "pet friendly",
        "concierge", "valet parking", "elevator", "business center", "dog park", 
        "basketball court", "bbq area", "lounge", "biking trails", "community park",
        "resort style", "spa", "sauna"
    ]
}

formatted_terms = []
term_counter = 1

for category, terms in taxonomy_data.items():
    for term in terms:
        formatted_terms.append({
            "id": f"term_{term_counter:03d}",
            "term": term,
            "category": category
        })
        term_counter += 1

taxonomy_json_structure = {
    "metadata": {
        "description": "Real estate terminology taxonomy across 8 categories.",
        "total_terms": len(formatted_terms)
    },
    "terms": formatted_terms
}

os.makedirs('data/processed', exist_ok=True)

output_path = 'data/processed/taxonomy.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(taxonomy_json_structure, f, indent=4)
