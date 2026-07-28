"""
assessment/forms.py

CSV grade upload form. Expected CSV columns (header row required):
    student_id, subject_code, ca_score, exam_score

Example:
    student_id,subject_code,ca_score,exam_score
    SCH-2026-0001,MATH101,32,55
    SCH-2026-0002,MATH101,28,49

- student_id must match an existing Student.student_id exactly.
- subject_code must match an existing Subject.code exactly.
- ca_score is out of 40, exam_score is out of 60 (adjust in
  assessment/models.py if your school uses a different split).
"""

from django import forms
from academics.models import Term


class ResultCSVUploadForm(forms.Form):
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(), widget=forms.Select(attrs={"class": "form-select"})
    )
    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
        help_text="Header row required: student_id, subject_code, ca_score, exam_score"
    )

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File too large (max 5MB).")
        return f
