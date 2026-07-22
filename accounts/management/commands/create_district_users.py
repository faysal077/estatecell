from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile, UserRole

DISTRICTS = [
    "Dhaka",
    "Faridpur",
    "Gazipur",
    "Gopalganj",
    "Jamalpur",
    "Kishoreganj",
    "Madaripur",
    "Manikganj",
    "Munshiganj",
    "Mymensingh",
    "Narayanganj",
    "Narsingdi",
    "Netrokona",
    "Rajbari",
    "Shariatpur",
    "Sherpur",
    "Tangail",

    "Bogra",
    "Joypurhat",
    "Naogaon",
    "Natore",
    "Nawabganj",
    "Pabna",
    "Rajshahi",
    "Sirajgonj",

    "Dinajpur",
    "Gaibandha",
    "Kurigram",
    "Lalmonirhat",
    "Nilphamari",
    "Panchagarh",
    "Rangpur",
    "Thakurgaon",

    "Barguna",
    "Barisal",
    "Bhola",
    "Jhalokati",
    "Patuakhali",
    "Pirojpur",

    "Bandarban",
    "Brahmanbaria",
    "Chandpur",
    "Chittagong",
    "Comilla",
    "CoxsBazar",
    "Feni",
    "Khagrachari",
    "Lakshmipur",
    "Noakhali",
    "Rangamati",

    "Habiganj",
    "Maulvibazar",
    "Sunamganj",
    "Sylhet",

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
]


class Command(BaseCommand):

    help = "Create all District Data Entry Users"

    def handle(self, *args, **kwargs):

        created = 0
        updated = 0

        for district in DISTRICTS:

            username = f"Estate_{district}"
            email = f"estate_{district.lower()}@bscic.gov.bd"
            password = f"{district.lower()}_12345"

            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": False,
                    "is_superuser": False,
                    "is_active": True,
                }
            )

            if user_created:
                user.set_password(password)
                user.save()
                created += 1
            else:
                updated += 1

            profile, _ = UserProfile.objects.get_or_create(
                user=user
            )

            profile.role = UserRole.DATA_ENTRY
            profile.department = district
            profile.full_name = f"{district} Estate Office"
            profile.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ {username} created/updated"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n-------------------------------------"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created : {created}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Existing : {updated}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Done."
            )
        )