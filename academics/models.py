"""
academics/models.py

The academic "scaffolding" that everything else (results, fees,
report cards) hangs off: departments, subjects, classes/streams,
sessions and terms.
"""

from django.db import models
from django.conf import settings


class Department(models.Model):
    """The 5 departments from the blueprint (Science, Languages, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="departments_headed"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")
    is_core = models.BooleanField(default=True, help_text="Core (compulsory) subject vs elective.")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicSession(models.Model):
    """e.g. '2025/2026'. Only one should be marked current at a time."""
    name = models.CharField(max_length=20, unique=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(models.Model):
    class TermName(models.TextChoices):
        FIRST = "1", "First Term"
        SECOND = "2", "Second Term"
        THIRD = "3", "Third Term"

    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=1, choices=TermName.choices)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ("session", "name")
        ordering = ["session", "name"]

    def __str__(self):
        return f"{self.get_name_display()} - {self.session}"

    def save(self, *args, **kwargs):
        if self.is_current:
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class SchoolClass(models.Model):
    """
    A stream, e.g. '7A', '10C'. Grades 7-9 = Upper Basic,
    10-12 = Senior Secondary, matching the blueprint's 7A-7F ... 12A-12F.
    """
    GRADE_CHOICES = [(str(g), f"Grade {g}") for g in range(7, 13)]
    STREAM_CHOICES = [(s, s) for s in "ABCDEF"]

    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    stream = models.CharField(max_length=1, choices=STREAM_CHOICES)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="classes_managed"
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name="classes")

    class Meta:
        unique_together = ("grade", "stream")
        ordering = ["grade", "stream"]

    @property
    def label(self):
        return f"{self.grade}{self.stream}"

    def __str__(self):
        return self.label


class TeacherAssignment(models.Model):
    """Which teacher teaches which subject to which class."""
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teaching_assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("teacher", "subject", "school_class")

    def __str__(self):
        return f"{self.teacher} - {self.subject} - {self.school_class}"


class TimetableSlot(models.Model):
    """
    A single period on the timetable. Kept as a straightforward
    manually-editable model (day/period/room) rather than an
    auto-generation algorithm -- staff assign slots and the system
    flags clashes (see clean()).
    """
    DAY_CHOICES = [
        ("MON", "Monday"), ("TUE", "Tuesday"), ("WED", "Wednesday"),
        ("THU", "Thursday"), ("FRI", "Friday"),
    ]
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="timetable_slots")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    period = models.PositiveSmallIntegerField(help_text="Period number, e.g. 1-8")
    room = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["day", "period"]

    def __str__(self):
        return f"{self.school_class} - {self.subject} ({self.get_day_display()} P{self.period})"

    def clean(self):
        from django.core.exceptions import ValidationError
        clash = TimetableSlot.objects.filter(
            teacher=self.teacher, day=self.day, period=self.period
        ).exclude(pk=self.pk)
        if clash.exists():
            raise ValidationError("This teacher already has a class scheduled in this period -- timetable clash.")
