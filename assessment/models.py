"""
assessment/models.py

Continuous Assessment (CA) + Exam scores roll up into a Result per
student/subject/term, which is what report cards and transcripts are
built from.

Grading scale (typical Gambian secondary scale, adjust in one place
if your school uses a different one):
  90-100 A1 | 80-89 B2 | 70-79 B3 | 65-69 C4 | 60-64 C5 | 55-59 C6
  50-54 D7  | 40-49 E8 | 0-39  F9
"""

from django.db import models
from django.conf import settings
from academics.models import Subject, Term, SchoolClass
from students.models import Student


def grade_from_score(total):
    scale = [
        (90, "A1", "Excellent"), (80, "B2", "Very Good"), (70, "B3", "Good"),
        (65, "C4", "Credit"), (60, "C5", "Credit"), (55, "C6", "Credit"),
        (50, "D7", "Pass"), (40, "E8", "Pass"), (0, "F9", "Fail"),
    ]
    for threshold, grade, remark in scale:
        if total >= threshold:
            return grade, remark
    return "F9", "Fail"


class Result(models.Model):
    """
    One row = one student's performance in one subject for one term.
    CA is out of 40, Exam out of 60 (standard 40/60 split) -- adjust
    max values below if your school uses a different weighting.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="results")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="results")

    ca_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Continuous Assessment, out of 40")
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Examination score, out of 60")

    teacher_remark = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    entered_on = models.DateTimeField(auto_now_add=True)
    is_moderated = models.BooleanField(default=False, help_text="Ticked once a senior teacher/HoD has moderated this score.")

    class Meta:
        unique_together = ("student", "subject", "term")
        ordering = ["student", "subject"]

    @property
    def total_score(self):
        return self.ca_score + self.exam_score

    @property
    def grade(self):
        return grade_from_score(self.total_score)[0]

    @property
    def remark(self):
        return grade_from_score(self.total_score)[1]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term}: {self.total_score}"


class ResultUploadLog(models.Model):
    """
    Keeps a record of every CSV grade upload so the Principal/Senior
    Teacher can see who uploaded what, and so a bad file can be traced
    back later. Doesn't store the file itself -- just the outcome.
    """
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    rows_total = models.PositiveIntegerField(default=0)
    rows_success = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_details = models.TextField(blank=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_on"]

    def __str__(self):
        return f"{self.file_name} - {self.term} ({self.rows_success}/{self.rows_total} ok)"


class ReportCard(models.Model):

    """
    One per student per term -- an aggregation record so we can cache
    the class position / average once computed, and track who
    generated + when. The actual PDF is generated on demand from
    Result rows (see utils.py) but we keep this model so students can
    only download once staff have marked the term's results 'ready'.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards")
    class_teacher_comment = models.TextField(blank=True)
    principal_comment = models.TextField(blank=True)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    class_position = models.PositiveIntegerField(null=True, blank=True)
    attendance_total_days = models.PositiveIntegerField(null=True, blank=True)
    attendance_present_days = models.PositiveIntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False, help_text="Must be ticked before the student can download it.")
    generated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "term")

    def __str__(self):
        return f"Report Card: {self.student} - {self.term}"
