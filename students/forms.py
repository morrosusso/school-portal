from django import forms
from django.contrib.auth import get_user_model
from .models import Application, Student, ApplicantDocument

User = get_user_model()


class ApplicantSignupForm(forms.Form):
    """
    Step 1 of the applicant flow: just enough to create a login --
    full name, email, password, gender. The rest of the admission
    details (DOB, guardian info, grade applying for) are filled in
    afterwards, once logged in, on the Applicant Dashboard.
    """
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}))
    gender = forms.ChoiceField(choices=Application.Gender.choices, widget=forms.Select(attrs={"class": "form-select"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists -- try logging in instead.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("confirm_password") and cleaned["password"] != cleaned["confirm_password"]:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


class ApplicationForm(forms.ModelForm):
    """
    Step 2: the full admission details, filled in by the applicant
    once they're logged in (see students/views.py -> applicant_dashboard).
    Required=True is enforced here at the FORM level even though the
    underlying model fields allow blank -- that's what lets the bare
    signup step (name/email/gender only) save successfully before
    this step is completed.
    """
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))

    class Meta:
        model = Application
        fields = [
            "date_of_birth", "guardian_name", "guardian_phone", "guardian_email", "address",
            "applying_for_grade", "applying_for_track", "previous_school", "passport_photo",
        ]
        widgets = {
            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_phone": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "applying_for_grade": forms.Select(attrs={"class": "form-select", "id": "id_applying_for_grade"}),
            "applying_for_track": forms.Select(attrs={"class": "form-select", "id": "id_applying_for_track"}),
            "previous_school": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["guardian_name", "guardian_phone", "address", "applying_for_grade"]:
            self.fields[name].required = True


class ApplicantDocumentForm(forms.ModelForm):
    class Meta:
        model = ApplicantDocument
        fields = ["label", "file"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Grade 6 Result Slip"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
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
