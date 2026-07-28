"""communication/models.py -- Notice board + internal messaging (simple, extensible)."""

from django.db import models
from django.conf import settings
from accounts.models import Role


class Notice(models.Model):
    class Audience(models.TextChoices):
        ALL = "ALL", "Everyone"
        STAFF = "STAFF", "All Staff"
        TEACHERS = "TEACHERS", "Teachers Only"
        STUDENTS = "STUDENTS", "Students Only"
        PARENTS = "PARENTS", "Parents Only"

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.ALL)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    posted_on = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-posted_on"]

    def __str__(self):
        return self.title

    def visible_to(self, user):
        if self.audience == self.Audience.ALL:
            return True
        if self.audience == self.Audience.STAFF:
            return user.role != Role.PARENT and user.role != Role.STUDENT
        if self.audience == self.Audience.TEACHERS:
            return user.role in (Role.TEACHER, Role.SENIOR_TEACHER)
        if self.audience == self.Audience.STUDENTS:
            return user.role == Role.STUDENT
        if self.audience == self.Audience.PARENTS:
            return user.role == Role.PARENT
        return False


class DirectMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField()
    sent_on = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_on"]

    def __str__(self):
        return f"{self.sender} -> {self.recipient}"
