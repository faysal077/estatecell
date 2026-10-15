
import os
import sys
import json
from pathlib import Path

import django
from django.db import transaction


# --------------------------------------------------
# 1. Initialize Django
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "esate_db.settings",
)

django.setup()

from industrial_estate.models import District, Upazila


# --------------------------------------------------
# 2. JSON file paths
# --------------------------------------------------

DISTRICTS_FILE = BASE_DIR / "data" / "bd-districts.json"
UPAZILAS_FILE = BASE_DIR / "data" / "bd-upazilas.json"


# --------------------------------------------------
# 3. Load JSON
# --------------------------------------------------

def load_json(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# --------------------------------------------------
# 4. Import upazilas
# --------------------------------------------------

def main():
    print("=" * 55)
    print("Upazila Import Started")
    print("=" * 55)

    # Load source data
    districts_json = load_json(DISTRICTS_FILE)
    upazilas_json = load_json(UPAZILAS_FILE)

    districts_data = districts_json.get("districts", [])
    upazilas_data = upazilas_json.get("upazilas", [])

    if not districts_data:
        print("ERROR: No districts found in district JSON.")
        sys.exit(1)

    if not upazilas_data:
        print("ERROR: No upazilas found in upazila JSON.")
        print("Please check the JSON structure.")
        sys.exit(1)

    # Map source district IDs to district names
    source_districts = {
        str(item["id"]).strip(): item["name"].strip()
        for item in districts_data
        if item.get("id") is not None and item.get("name")
    }

    # Map existing database districts by name
    database_districts = {
        district.name.strip(): district
        for district in District.objects.all()
    }

    missing_districts = set()
    valid_records = []
    invalid_records = 0

    # Validate upazila records
    for item in upazilas_data:
        source_district_id = item.get("district_id")
        upazila_name = item.get("name")

        if source_district_id is None or not upazila_name:
            invalid_records += 1
            continue

        source_district_id = str(source_district_id).strip()
        district_name = source_districts.get(source_district_id)

        if not district_name:
            missing_districts.add(
                f"Unknown source district ID: {source_district_id}"
            )
            continue

        district = database_districts.get(district_name)

        if district is None:
            missing_districts.add(district_name)
            continue

        upazila_name = upazila_name.strip()

        if upazila_name:
            valid_records.append((district, upazila_name))
        else:
            invalid_records += 1

    # Remove duplicate records from the import list
    valid_records = list({
        (district.pk, name): (district, name)
        for district, name in valid_records
    }.values())

    # Show import summary
    print(f"Source districts: {len(source_districts)}")
    print(f"Database districts: {len(database_districts)}")
    print(f"JSON upazilas: {len(upazilas_data)}")
    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {invalid_records}")

    if missing_districts:
        print("\nDistricts requiring attention:")
        for name in sorted(missing_districts):
            print(f" - {name}")

        print(
            "\nIMPORT CANCELLED: Some districts could not be matched. "
            "No upazilas were imported."
        )
        sys.exit(1)

    if not valid_records:
        print("\nNo valid upazila records found. Nothing imported.")
        sys.exit(1)

    # Import records inside a database transaction
    created_count = 0
    existing_count = 0

    with transaction.atomic():
        for district, name in valid_records:
            _, created = Upazila.objects.get_or_create(
                district=district,
                name=name,
            )

            if created:
                created_count += 1
            else:
                existing_count += 1

    print("\n" + "=" * 55)
    print("IMPORT COMPLETED SUCCESSFULLY")
    print("=" * 55)
    print(f"New upazilas imported: {created_count}")
    print(f"Already existing: {existing_count}")
    print(f"Total upazilas in database: {Upazila.objects.count()}")


if __name__ == "__main__":
    main()
