"""library_mgmt/models.py -- Library catalog + borrow/return tracking."""

from django.db import models
from django.conf import settings
from students.models import Student


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    isbn = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)

    @property
    def copies_available(self):
        borrowed = self.borrow_records.filter(returned_on__isnull=True).count()
        return self.total_copies - borrowed

    def __str__(self):
        return self.title


class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrow_records")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="borrow_records")
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    borrowed_on = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_on = models.DateField(null=True, blank=True)

    @property
    def is_overdue(self):
        from django.utils import timezone
        return not self.returned_on and timezone.localdate() > self.due_date

    def __str__(self):
        return f"{self.book} -> {self.student}"
