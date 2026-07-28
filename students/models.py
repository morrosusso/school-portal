"""
students/models.py

Two-stage flow:
  1. Application  -- anyone can submit one (public form, no login needed).
  2. Student       -- created automatically, with an auto-generated
                       Student ID, the moment an Application's status
                       is changed to ACCEPTED. See signals.py.

This matches the requirement: "students get automatic id after
their application is accepted".
"""

import datetime
from django.db import models
from django.conf import settings
from academics.models import SchoolClass


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True)
    address = models.CharField(max_length=255)
    applying_for_grade = models.CharField(max_length=2, choices=SchoolClass.GRADE_CHOICES)
    previous_school = models.CharField(max_length=150, blank=True)
    passport_photo = models.ImageField(upload_to="applicant_photos/", blank=True, null=True)
    submitted_on = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="applications_reviewed"
    )
    reviewed_on = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-submitted_on"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"


class Student(models.Model):
    """
    Created automatically (see signals.py) the instant an Application
    is accepted. student_id format: SCH-<year>-<sequence>, e.g.
    SCH-2026-0001.
    """
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name="student_record")
    student_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile", null=True, blank=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Application.Gender.choices)
    guardian_name = models.CharField(max_length=150)
    guardian_phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    passport_photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)

    current_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    date_admitted = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"

    @staticmethod
    def generate_student_id():
        """
        SCH-<year>-<4-digit sequence>. Sequence resets each calendar
        year. Wrapped in a transaction with select_for_update at the
        call site (signals.py) to stay safe under concurrent accepts.
        """
        year = datetime.date.today().year
        prefix = f"SCH-{year}-"
        last = Student.objects.filter(student_id__startswith=prefix).order_by("-student_id").first()
        next_seq = 1 if not last else int(last.student_id.split("-")[-1]) + 1
        return f"{prefix}{next_seq:04d}"


class DisciplineRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="discipline_records")
    date = models.DateField()
    description = models.TextField()
    action_taken = models.CharField(max_length=255, blank=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.date}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"
