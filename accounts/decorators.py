# from functools import wraps
# from django.shortcuts import redirect
# from accounts.models import UserProfile


# def role_required(*roles):

#     def decorator(view_func):

#         @wraps(view_func)
#         def wrapper(request, *args, **kwargs):

#             profile, _ = UserProfile.objects.get_or_create(
#                 user=request.user
#             )

#             if profile.role in roles:
#                 return view_func(request, *args, **kwargs)

#             return redirect("dashboard")

#         return wrapper

#     return decorator


from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

from accounts.models import UserProfile


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Require authentication first
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            # Inactive users must not access protected views
            if not request.user.is_active:
                return redirect("dashboard")

            # Read the existing profile; do not create one here
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                return redirect("dashboard")

            # Allow any user whose role matches
            if profile.role in roles:
                return view_func(request, *args, **kwargs)

            return redirect("dashboard")

        return wrapper

    return decorator
