# districts utility - serves district choices from bd-districts.json
import json, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / 'data' / 'bd-districts.json'

# Division mapping
DIVISION_NAMES = {
    "1": "Barishal", "2": "Chattogram", "3": "Dhaka",
    "4": "Khulna", "5": "Rajshahi", "6": "Rangpur",
    "7": "Sylhet", "8": "Mymensingh"
}

# Load districts from JSON
def get_districts():
    if JSON_PATH.exists():
        with open(JSON_PATH, encoding='utf-8') as f:
            return json.load(f).get('districts', [])
    return []

DISTRICTS = get_districts()

# (value, display) choices for Django form Select
DISTRICT_CHOICES = [(d['name'], d['name']) for d in DISTRICTS]
# Include bn_name for display
DISTRICT_CHOICES_WITH_BN = [(d['name'], f"{d['name']} ({d['bn_name']})") for d in DISTRICTS]

# Build lookup dict: name -> full record
DISTRICT_LOOKUP = {d['name']: d for d in DISTRICTS}

def get_district_by_name(name):
    """Case-insensitive district lookup."""
    return DISTRICT_LOOKUP.get(name) or next(
        (d for d in DISTRICTS if d['name'].lower() == name.lower()), None
    )

def get_district_id(name):
    """Get district ID by name."""
    d = get_district_by_name(name)
    return d['id'] if d else None
