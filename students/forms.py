from django import forms
from .models import Application, Student


class ApplicationForm(forms.ModelForm):
    """Public admission-application form -- no login required."""
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))

    class Meta:
        model = Application
        fields = [
            "first_name", "last_name", "date_of_birth", "gender", "guardian_name",
            "guardian_phone", "guardian_email", "address", "applying_for_grade", "applying_for_track",
            "previous_school", "passport_photo",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "applying_for_grade": forms.Select(attrs={"class": "form-select", "id": "id_applying_for_grade"}),
            "applying_for_track": forms.Select(attrs={"class": "form-select", "id": "id_applying_for_track"}),
            "previous_school": forms.TextInput(attrs={"class": "form-control"}),
        }


class ApplicationReviewForm(forms.ModelForm):
    """Used by Secretary/Principal/VP to accept or reject an application."""
    class Meta:
        model = Application
        fields = ["status", "review_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "review_notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class StudentClassAssignForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["current_class"]
        widgets = {"current_class": forms.Select(attrs={"class": "form-select"})}
