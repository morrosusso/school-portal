"""
accounts/forms.py

Login uses Django's built-in AuthenticationForm (no need to reinvent
it). This file just adds Bootstrap-friendly widgets via widget_tweaks
in the template, and a staff-creation form used by admin-permission
users who prefer a friendlier form over the raw /admin/ page.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, StaffProfile


class PortalLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Username", "autofocus": True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control", "placeholder": "Password"
    }))


class StaffCreationForm(forms.ModelForm):
    """Used by admin-permission users to onboard new staff accounts."""
    password = forms.CharField(widget=forms.PasswordInput, help_text="Temporary password -- staff should change it after first login.")
    staff_id = forms.CharField(max_length=20)
    qualification = forms.ChoiceField(choices=StaffProfile.Qualification.choices, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone_number", "role", "password"]
        widgets = {f: forms.TextInput(attrs={"class": "form-control"}) for f in
                   ["username", "first_name", "last_name", "email", "phone_number"]}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            StaffProfile.objects.create(
                user=user,
                staff_id=self.cleaned_data["staff_id"],
                qualification=self.cleaned_data.get("qualification", ""),
            )
        return user
