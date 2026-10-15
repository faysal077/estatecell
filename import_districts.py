
import os
import json
from pathlib import Path

import django

# Django settings load
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "esate_db.settings")
django.setup()

from industrial_estate.models import District

# Project root directory
BASE_DIR = Path(__file__).resolve().parent
json_path = BASE_DIR / "data" / "bd-districts.json"

if not json_path.exists():
    raise FileNotFoundError(f"JSON file not found: {json_path}")

with json_path.open("r", encoding="utf-8") as file:
    data = json.load(file)

districts_data = data.get("districts", [])

if not districts_data:
    raise ValueError("No district data found in the JSON file.")

created_count = 0
existing_count = 0

for item in districts_data:
    name = item["name"].strip()

    district, created = District.objects.get_or_create(
        name=name
    )

    if created:
        created_count += 1
    else:
        existing_count += 1

print("\nDistrict import completed.")
print("New districts added:", created_count)
print("Already existing:", existing_count)
print("Total districts in database:", District.objects.count())
