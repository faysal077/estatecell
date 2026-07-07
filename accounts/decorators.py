from functools import wraps
from django.shortcuts import redirect
from accounts.models import UserProfile


def role_required(*roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            profile, _ = UserProfile.objects.get_or_create(
                user=request.user
            )

            if profile.role in roles:
                return view_func(request, *args, **kwargs)

            return redirect("dashboard")

        return wrapper

    return decorator