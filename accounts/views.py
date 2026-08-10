from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from .models import UserProfile, UserRole 
from .forms import FirstPasswordChangeForm
from .models import UserProfile, UserRole, PasswordChangeLog
# -----------------------------
# 🔑 USER LOGIN
# -----------------------------
# def user_login(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             login(request, user)
#             messages.success(request, "Login successful!")
#             return redirect("dashboard")  # Landing page after login
#         else:
#             messages.error(request, "Invalid username or password.")

#     return render(request, "accounts/login.html")

# def user_login(request):
#     if request.user.is_authenticated:
#         return redirect("dashboard")

#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             login(request, user)
#             return redirect("dashboard")
#         else:
#             messages.error(request, "Invalid username or password.")

#     return render(request, "accounts/login.html")
def user_login(request):
    # If already logged in
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Get or create user profile
            profile, _ = UserProfile.objects.get_or_create(
                user=user
            )

            # Force password change for DATA_ENTRY users
            if (
                profile.role == UserRole.DATA_ENTRY
                and profile.must_change_password
            ):
                messages.warning(
                    request,
                    "Please change your temporary password first."
                )

                return redirect(
                    "accounts:first_password_change"
                )

            # Normal login
            messages.success(
                request,
                "Login successful!"
            )

            return redirect("dashboard")

        else:
            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "accounts/login.html"
    )
# -----------------------------
# 🔐 FIRST TIME PASSWORD CHANGE
# -----------------------------

# @login_required
# def first_password_change(request):
#     profile = request.user.userprofile

#     # Only DATA_ENTRY users can use this page
#     if profile.role != UserRole.DATA_ENTRY:
#         return redirect("dashboard")

#     # If already changed, skip
#     if not profile.must_change_password:
#         return redirect("dashboard")

#     form = FirstPasswordChangeForm(request.POST or None)

#     if request.method == "POST" and form.is_valid():
#         new_password = form.cleaned_data["new_password"]

#         # Set new password
#         request.user.set_password(new_password)
#         request.user.save()

#         # Mark password as changed
#         profile.must_change_password = False
#         profile.save()

#         # Logout user after password change
#         logout(request)

#         messages.success(
#             request,
#             "Password changed successfully. Please login again."
#         )

#         return redirect("accounts:login")

#     return render(
#         request,
#         "accounts/first_password_change.html",
#         {
#             "form": form
#         }
#     )
@login_required
def first_password_change(request):
    profile = request.user.userprofile

    # Only DATA_ENTRY users can access
    if profile.role != UserRole.DATA_ENTRY:
        return redirect("dashboard")

    # Already changed
    if not profile.must_change_password:
        return redirect("dashboard")

    form = FirstPasswordChangeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        new_password = form.cleaned_data["new_password"]

        # Change password
        request.user.set_password(new_password)
        request.user.save()

        # Mark as changed
        profile.must_change_password = False
        profile.save()

        # Create audit log
        # PasswordChangeLog.objects.create(
        #     user=request.user,
        #     changed_by=request.user,
        #     ip_address=get_client_ip(request),
        #     user_agent=request.META.get("HTTP_USER_AGENT", ""),
        # )

        # ------------------------------
        # CREATE PASSWORD CHANGE LOG
        # ------------------------------
        PasswordChangeLog.objects.create(
            user=request.user,
            changed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        # Logout user
        logout(request)

        messages.success(
            request,
            "Password changed successfully. Please login again.",
        )

        return redirect("accounts:login")

    return render(
        request,
        "accounts/first_password_change.html",
        {"form": form},
    )
# -----------------------------
# 🔒 Client IP
# -----------------------------
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

# -----------------------------
# 🔒 USER LOGOUT
# -----------------------------
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


# -----------------------------
# 📝 USER REGISTRATION
# -----------------------------
def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("accounts:register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("accounts:register")

        # Create User
        user = User.objects.create_user(username=username, password=password1)
        user.save()

        messages.success(request, "Registration successful! Please login.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html")


# -----------------------------
# 👤 USER PROFILE
# -----------------------------
@login_required
def user_profile(request):
    return render(request, "accounts/profile.html")


# -----------------------------
# 🔄 PASSWORD CHANGE
# -----------------------------
@login_required
def password_change(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("accounts:password_change")

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("accounts:password_change")

        user.set_password(new_password)
        user.save()

        # Keep the user logged in after changing password
        update_session_auth_hash(request, user)

        messages.success(request, "Password changed successfully.")
        return redirect("accounts:profile")

    return render(request, "accounts/password_change.html")
