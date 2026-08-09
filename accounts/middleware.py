from django.shortcuts import redirect
from django.contrib import messages

from esate_db import settings


class AdminAccessMiddleware:
    """
    Only Django Superusers can access /admin/.
    All other authenticated users are redirected.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Protect Django Admin URLs
        if request.path.startswith(settings.ADMIN_URL):

            # User is not logged in
            if not request.user.is_authenticated:
                return redirect("accounts:login")   # Change if your login URL name is different

            # Only Django Superusers can access
            if not request.user.is_superuser:
                messages.error(
                    request,
                    "You are not authorized to access the System Administration Panel."
                )
                return redirect("lands:land_list")

        return self.get_response(request)