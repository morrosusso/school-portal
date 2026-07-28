"""
accounts/views.py

Handles login/logout and staff onboarding. The dashboard routing
itself lives in core/views.py so accounts stays focused on identity.
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import PortalLoginForm, StaffCreationForm
from .models import Role


class PortalLoginView(auth_views.LoginView):
    """Custom-styled login page shared by every role."""
    template_name = "accounts/login.html"
    authentication_form = PortalLoginForm
    redirect_authenticated_user = True


def is_admin_permission_user(user):
    return user.is_authenticated and user.is_admin_permission


@login_required
@user_passes_test(is_admin_permission_user, login_url="core:dashboard")
def add_staff(request):
    """
    Admin-permission staff (Principal, VPs, Senior Teachers, Secretary,
    IT Support) can create new staff logins without touching /admin/.
    """
    if request.method == "POST":
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff account created for {user.get_full_name()} ({user.username}).")
            return redirect("accounts:add_staff")
    else:
        form = StaffCreationForm()
    return render(request, "accounts/add_staff.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})
