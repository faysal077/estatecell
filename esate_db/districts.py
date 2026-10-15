# # districts utility - serves district choices from bd-districts.json
# import json, os
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# JSON_PATH = BASE_DIR / 'data' / 'bd-districts.json'

# # Division mapping
# DIVISION_NAMES = {
#     "1": "------Select Division------", 
#     "2": "ঢাকা", "3": "চট্টগ্রাম", "4": "খুলনা", 
#     "5": "রাজশাহী", "6": "রংপুর", "7": "সিলেট", "8": "ময়মনসিংহ", "9": "বরিশাল", 
    
# }

# # Load districts from JSON
# def get_districts():
#     if JSON_PATH.exists():
#         with open(JSON_PATH, encoding='utf-8') as f:
#             return json.load(f).get('districts', [])
#     return []

# DISTRICTS = get_districts()

# # (value, display) choices for Django form Select
# DISTRICT_CHOICES = [(d['name'], d['name']) for d in DISTRICTS]
# # Include bn_name for display
# DISTRICT_CHOICES_WITH_BN = [(d['name'], f"{d['name']} ({d['bn_name']})") for d in DISTRICTS]

# # Build lookup dict: name -> full record
# DISTRICT_LOOKUP = {d['name']: d for d in DISTRICTS}

# def get_district_by_name(name):
#     """Case-insensitive district lookup."""
#     return DISTRICT_LOOKUP.get(name) or next(
#         (d for d in DISTRICTS if d['name'].lower() == name.lower()), None
#     )

# def get_district_id(name):
#     """Get district ID by name."""
#     d = get_district_by_name(name)
#     return d['id'] if d else None


# esate_db/districts.py
"""
Location utilities for Bangladesh.

Preserves the existing JSON-based district data and helper functions,
while providing division-to-district mapping and bilingual dropdown labels.

Existing JSON file:
    data/bd-districts.json
"""

import json
from pathlib import Path


# ---------------------------------------------------------
# 1. Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "data" / "bd-districts.json"


# ---------------------------------------------------------
# 2. Division names
#    Key = division code
#    Value = Bangla name
# ---------------------------------------------------------

DIVISION_NAMES = {
    "1": "------Select Division------",
    "2": "ঢাকা",
    "3": "চট্টগ্রাম",
    "4": "খুলনা",
    "5": "রাজশাহী",
    "6": "রংপুর",
    "7": "সিলেট",
    "8": "ময়মনসিংহ",
    "9": "বরিশাল",
}


# English division name -> Bangla division name.
# These keys are used by the dependent dropdown.
DIVISION_NAMES_EN_BN = {
    "Barisal": "বরিশাল",
    "Chittagong": "চট্টগ্রাম",
    "Dhaka": "ঢাকা",
    "Khulna": "খুলনা",
    "Mymensingh": "ময়মনসিংহ",
    "Rajshahi": "রাজশাহী",
    "Rangpur": "রংপুর",
    "Sylhet": "সিলেট",
}


# Division code -> English division name.
DIVISION_CODE_TO_EN = {
    "2": "Dhaka",
    "3": "Chittagong",
    "4": "Khulna",
    "5": "Rajshahi",
    "6": "Rangpur",
    "7": "Sylhet",
    "8": "Mymensingh",
    "9": "Barisal",
}


# ---------------------------------------------------------
# 3. Division -> District mapping
#
# District names here follow the names in your supplied list.
# They must match District.name values in your Django database
# if you use this mapping to filter database records.
# ---------------------------------------------------------

DIVISION_DISTRICT_MAP = {
    "Barisal": [
        "Barguna",
        "Barisal",
        "Bhola",
        "Jhalokati",
        "Patuakhali",
        "Pirojpur",
    ],

    "Chittagong": [
        "Bandarban",
        "Brahmanbaria",
        "Chandpur",
        "Chittagong",
        "Comilla",
        "Cox's Bazar",
        "Feni",
        "Khagrachhari",
        "Lakshmipur",
        "Noakhali",
        "Rangamati",
    ],

    "Dhaka": [
        "Dhaka",
        "Faridpur",
        "Gazipur",
        "Gopalganj",
        "Kishoreganj",
        "Madaripur",
        "Manikganj",
        "Munshiganj",
        "Narayanganj",
        "Narsingdi",
        "Rajbari",
        "Shariatpur",
        "Tangail",
    ],

    "Khulna": [
        "Bagerhat",
        "Chuadanga",
        "Jessore",
        "Jhenaidah",
        "Khulna",
        "Kushtia",
        "Magura",
        "Meherpur",
        "Narail",
        "Satkhira",
    ],

    "Mymensingh": [
        "Jamalpur",
        "Mymensingh",
        "Netrakona",
        "Sherpur",
    ],

    "Rajshahi": [
        "Bogra",
        "Chapainawabganj",
        "Joypurhat",
        "Naogaon",
        "Natore",
        "Pabna",
        "Rajshahi",
        "Sirajganj",
    ],

    "Rangpur": [
        "Dinajpur",
        "Gaibandha",
        "Kurigram",
        "Lalmonirhat",
        "Nilphamari",
        "Panchagarh",
        "Rangpur",
        "Thakurgaon",
    ],

    "Sylhet": [
        "Habiganj",
        "Moulvibazar",
        "Sunamganj",
        "Sylhet",
    ],
}


# ---------------------------------------------------------
# 4. District English -> Bangla names
# ---------------------------------------------------------

DISTRICT_NAMES_BN = {
    "Barguna": "বরগুনা",
    "Barisal": "বরিশাল",
    "Bhola": "ভোলা",
    "Jhalokati": "ঝালকাঠি",
    "Patuakhali": "পটুয়াখালী",
    "Pirojpur": "পিরোজপুর",

    "Bandarban": "বান্দরবান",
    "Brahmanbaria": "ব্রাহ্মণবাড়িয়া",
    "Chandpur": "চাঁদপুর",
    "Chittagong": "চট্টগ্রাম",
    "Comilla": "কুমিল্লা",
    "Cox's Bazar": "কক্সবাজার",
    "Feni": "ফেনী",
    "Khagrachhari": "খাগড়াছড়ি",
    "Lakshmipur": "লক্ষ্মীপুর",
    "Noakhali": "নোয়াখালী",
    "Rangamati": "রাঙ্গামাটি",

    "Dhaka": "ঢাকা",
    "Faridpur": "ফরিদপুর",
    "Gazipur": "গাজীপুর",
    "Gopalganj": "গোপালগঞ্জ",
    "Kishoreganj": "কিশোরগঞ্জ",
    "Madaripur": "মাদারীপুর",
    "Manikganj": "মানিকগঞ্জ",
    "Munshiganj": "মুন্সীগঞ্জ",
    "Narayanganj": "নারায়ণগঞ্জ",
    "Narsingdi": "নরসিংদী",
    "Rajbari": "রাজবাড়ী",
    "Shariatpur": "শরীয়তপুর",
    "Tangail": "টাঙ্গাইল",

    "Bagerhat": "বাগেরহাট",
    "Chuadanga": "চুয়াডাঙ্গা",
    "Jessore": "যশোর",
    "Jhenaidah": "ঝিনাইদহ",
    "Khulna": "খুলনা",
    "Kushtia": "কুষ্টিয়া",
    "Magura": "মাগুরা",
    "Meherpur": "মেহেরপুর",
    "Narail": "নড়াইল",
    "Satkhira": "সাতক্ষীরা",

    "Jamalpur": "জামালপুর",
    "Mymensingh": "ময়মনসিংহ",
    "Netrakona": "নেত্রকোণা",
    "Sherpur": "শেরপুর",

    "Bogra": "বগুড়া",
    "Chapainawabganj": "চাঁপাইনবাবগঞ্জ",
    "Joypurhat": "জয়পুরহাট",
    "Naogaon": "নওগাঁ",
    "Natore": "নাটোর",
    "Pabna": "পাবনা",
    "Rajshahi": "রাজশাহী",
    "Sirajganj": "সিরাজগঞ্জ",

    "Dinajpur": "দিনাজপুর",
    "Gaibandha": "গাইবান্ধা",
    "Kurigram": "কুড়িগ্রাম",
    "Lalmonirhat": "লালমনিরহাট",
    "Nilphamari": "নীলফামারী",
    "Panchagarh": "পঞ্চগড়",
    "Rangpur": "রংপুর",
    "Thakurgaon": "ঠাকুরগাঁও",

    "Habiganj": "হবিগঞ্জ",
    "Moulvibazar": "মৌলভীবাজার",
    "Sunamganj": "সুনামগঞ্জ",
    "Sylhet": "সিলেট",
}


# ---------------------------------------------------------
# 5. Load districts from existing JSON file
# ---------------------------------------------------------

def get_districts():
    """Load district records from bd-districts.json."""
    if not JSON_PATH.exists():
        return []

    try:
        with open(JSON_PATH, encoding="utf-8") as file:
            data = json.load(file)

        return data.get("districts", [])

    except (json.JSONDecodeError, OSError):
        return []


DISTRICTS = get_districts()


# ---------------------------------------------------------
# 6. Existing district choices - preserved
# ---------------------------------------------------------

DISTRICT_CHOICES = [
    (district["name"], district["name"])
    for district in DISTRICTS
    if district.get("name")
]


# English (Bangla) labels, using JSON data first.
DISTRICT_CHOICES_WITH_BN = [
    (
        district["name"],
        f'{district["name"]} '
        f'({district.get("bn_name") or DISTRICT_NAMES_BN.get(district["name"], district["name"])})',
    )
    for district in DISTRICTS
    if district.get("name")
]


# ---------------------------------------------------------
# 7. Existing lookup dictionary - preserved
# ---------------------------------------------------------

DISTRICT_LOOKUP = {
    district["name"]: district
    for district in DISTRICTS
    if district.get("name")
}


def get_district_by_name(name):
    """Case-insensitive district lookup."""
    if not name:
        return None

    return DISTRICT_LOOKUP.get(name) or next(
        (
            district
            for district in DISTRICTS
            if district.get("name", "").lower() == name.lower()
        ),
        None,
    )


def get_district_id(name):
    """Get district ID by name."""
    district = get_district_by_name(name)
    return district.get("id") if district else None


# ---------------------------------------------------------
# 8. Division choices: English (Bangla)
# ---------------------------------------------------------

DIVISION_CHOICES_WITH_BN = [
    (english, f"{english} ({bangla})")
    for english, bangla in DIVISION_NAMES_EN_BN.items()
]


# ---------------------------------------------------------
# 9. Helpers for division/district filtering
# ---------------------------------------------------------

def get_district_names_by_division(division_name):
    """Return district names for a division."""
    return DIVISION_DISTRICT_MAP.get(division_name, [])


def get_division_by_district(district_name):
    """Return the division name associated with a district."""
    if not district_name:
        return None

    for division_name, district_names in DIVISION_DISTRICT_MAP.items():
        if district_name in district_names:
            return division_name

    # Allow matching when capitalization differs.
    district_lower = district_name.strip().lower()

    for division_name, district_names in DIVISION_DISTRICT_MAP.items():
        if any(name.lower() == district_lower for name in district_names):
            return division_name

    return None
