"""
accounts/models.py

Custom User model for the portal. Every person who logs in -- from the
Principal to a Parent -- is a User with a `role`. The role drives:
  * which dashboard they land on after login (see core/views.py)
  * which menu items they see (see templates/base.html)
  * which sensitive actions they're allowed to do
    (e.g. only ADMIN_ROLES can download an official transcript)

Why one User model instead of separate tables per role?
Django's auth/permissions/login system is built around a single
AUTH_USER_MODEL. Keeping one model means login, password reset, and
permission checks all work the same way for everyone, while the
`role` field still lets us branch behaviour cleanly.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """Every user category from the school's blueprint document."""
    PRINCIPAL = "PRINCIPAL", "Principal"
    VICE_PRINCIPAL = "VICE_PRINCIPAL", "Vice Principal"
    SENIOR_TEACHER = "SENIOR_TEACHER", "Senior Teacher"
    TEACHER = "TEACHER", "Teacher"
    BURSAR = "BURSAR", "Bursar"
    SECRETARY = "SECRETARY", "Office Secretary"
    IT_SUPPORT = "IT_SUPPORT", "I.T Teacher / Support"
    LIBRARIAN = "LIBRARIAN", "Librarian"
    NON_TEACHING = "NON_TEACHING", "Non-Teaching Staff (Cleaner/Caretaker/Watchman)"
    PARENT = "PARENT", "Parent / Guardian"
    STUDENT = "STUDENT", "Student"
    CLUSTER_MONITOR = "CLUSTER_MONITOR", "Cluster Monitor (MoBSE)"


# Roles that count as "staff with admin permissions" -- these are the
# only accounts allowed to download official transcripts, per the
# requirement: "transcript will only be able to be downloaded by
# staff with admin permissions".
ADMIN_PERMISSION_ROLES = [
    Role.PRINCIPAL,
    Role.VICE_PRINCIPAL,
    Role.SENIOR_TEACHER,
    Role.SECRETARY,
    Role.IT_SUPPORT,
]

STAFF_ROLES = ADMIN_PERMISSION_ROLES + [Role.BURSAR, Role.LIBRARIAN, Role.NON_TEACHING, Role.TEACHER]


class User(AbstractUser):
    """
    Extends Django's built-in user with the fields the portal needs.
    Login is by username (auto-created) but we also store email/phone.
    """
    role = models.CharField(max_length=30, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    # Set automatically by save() -- kept as a real DB field (not just
    # a property) so it can be filtered on quickly and checked in
    # templates with `user.is_admin_permission`.
    is_admin_permission = models.BooleanField(default=False, editable=False)

    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.is_admin_permission = self.role in ADMIN_PERMISSION_ROLES
        # Django's is_staff flag controls access to /admin/ -- give it
        # automatically to every non-parent, non-student role so they
        # can use the Django admin as a power-user backend if needed.
        if self.role and self.role not in (Role.PARENT, Role.STUDENT):
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_teacher(self):
        return self.role in (Role.TEACHER, Role.SENIOR_TEACHER)

    class Meta:
        ordering = ["last_name", "first_name"]


class StaffProfile(models.Model):
    """
    Extra staff-only details from the blueprint (qualifications,
    department, posting history) that don't belong on the login
    model itself.
    """

    class Qualification(models.TextChoices):
        MASTERS = "MASTERS", "Master's Degree"
        BACHELORS = "BACHELORS", "Bachelor's Degree"
        HTC = "HTC", "HTC Only"
        HTC_PTC = "HTC_PTC", "HTC + PTC"
        PTC = "PTC", "PTC Only"
        MULTI = "MULTI", "Multi-Qualification (HTC + B.Ed + etc.)"
        OTHER = "OTHER", "Other / Non-Teaching"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    staff_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=20, choices=Qualification.choices, blank=True)
    department = models.ForeignKey(
        "academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="staff"
    )
    date_employed = models.DateField(blank=True, null=True)
    is_active_staff = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()}"


class ParentProfile(models.Model):
    """Links a parent/guardian login to their child(ren)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    students = models.ManyToManyField("students.Student", related_name="guardians", blank=True)
    relationship = models.CharField(max_length=30, default="Parent")

    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"
