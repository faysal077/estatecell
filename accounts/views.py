from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash


# -----------------------------
# 🔑 USER LOGIN
# -----------------------------
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")  # Landing page after login
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


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
