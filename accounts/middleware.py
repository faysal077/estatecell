from django.shortcuts import redirect
from django.contrib import messages
from esate_db import settings
import json
from django.contrib.auth.models import AnonymousUser
from django.urls import resolve

from .models import AuditLog, UserProfile

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
class AuditLogMiddleware:
    """
    Automatically records POST requests made to the application.

    Captures:
        - User
        - Role
        - Action / View
        - Request data
        - URL
        - IP address
        - User agent
        - Response status
        - Timestamp

    Sensitive values are automatically masked.
    """

    # Fields that should NEVER be stored in audit logs
    SENSITIVE_FIELDS = {
        "password",
        "password1",
        "password2",
        "old_password",
        "new_password",
        "confirm_password",
        "csrfmiddlewaretoken",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    # ---------------------------------------------------------
    # Client IP
    # ---------------------------------------------------------

    def get_client_ip(self, request):

        x_forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

    # ---------------------------------------------------------
    # Sanitize values
    # ---------------------------------------------------------

    def sanitize_value(self, key, value):

        key_lower = str(key).lower()

        # Never store sensitive fields
        if key_lower in self.SENSITIVE_FIELDS:
            return "[REDACTED]"

        if isinstance(value, list):
            return [
                self.sanitize_value(key, item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                k: self.sanitize_value(k, v)
                for k, v in value.items()
            }

        return value

    # ---------------------------------------------------------
    # Capture POST data
    # ---------------------------------------------------------

    def get_post_data(self, request):

        data = {}

        try:

            # Normal form / AJAX POST data
            if request.POST:

                for key in request.POST.keys():

                    values = request.POST.getlist(key)

                    if len(values) == 1:
                        data[key] = self.sanitize_value(
                            key,
                            values[0]
                        )

                    else:
                        data[key] = self.sanitize_value(
                            key,
                            values
                        )

            # -------------------------------------------------
            # Uploaded files
            # -------------------------------------------------

            if request.FILES:

                files = {}

                for key in request.FILES:

                    uploaded_files = request.FILES.getlist(key)

                    file_list = []

                    for uploaded_file in uploaded_files:

                        file_list.append({
                            "filename": uploaded_file.name,
                            "size": uploaded_file.size,
                            "content_type": uploaded_file.content_type,
                        })

                    files[key] = file_list

                data["_files"] = files

        except Exception as e:

            data = {
                "_audit_error": (
                    f"Could not parse request data: {str(e)}"
                )
            }

        return data

    # ---------------------------------------------------------
    # Get action name
    # ---------------------------------------------------------

    def get_action(self, request):

        try:

            match = resolve(request.path_info)

            view_name = match.view_name

            if view_name:
                return view_name

            if hasattr(match.func, "__name__"):
                return match.func.__name__

        except Exception:
            pass

        return request.path

    # ---------------------------------------------------------
    # Get user role
    # ---------------------------------------------------------

    def get_user_role(self, request):

        if not request.user.is_authenticated:
            return None

        try:

            profile = UserProfile.objects.get(
                user=request.user
            )

            return profile.role

        except UserProfile.DoesNotExist:

            return None

        except Exception:

            return None

    # ---------------------------------------------------------
    # Create audit record
    # ---------------------------------------------------------

    def create_log(
        self,
        request,
        response=None,
        exception=None,
    ):

        try:

            user = None

            if (
                hasattr(request, "user")
                and request.user.is_authenticated
            ):
                user = request.user

            role = self.get_user_role(request)

            action = self.get_action(request)

            request_data = self.get_post_data(request)

            # Record exception information if request failed
            if exception:

                request_data["_exception"] = str(exception)

            status_code = None

            if response is not None:
                status_code = response.status_code

            elif exception:
                status_code = 500

            AuditLog.objects.create(

                user=user,

                role=role,

                action=action,

                method=request.method,

                path=request.path,

                request_data=request_data,

                ip_address=self.get_client_ip(request),

                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    ""
                ),

                status_code=status_code,
            )

        except Exception:
            # Never allow audit logging to break
            # the actual application.
            pass

    # ---------------------------------------------------------
    # Middleware execution
    # ---------------------------------------------------------

    def __call__(self, request):

        # Only audit POST requests
        if request.method != "POST":
            return self.get_response(request)

        try:

            response = self.get_response(request)

            self.create_log(
                request=request,
                response=response,
            )

            return response

        except Exception as e:

            # Log failed request
            self.create_log(
                request=request,
                exception=e,
            )

            raise