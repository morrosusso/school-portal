"""finance/models.py -- Bursar module: fee setup, invoices, payments."""

from django.db import models
from django.conf import settings
from students.models import Student
from academics.models import Term


class FeeType(models.Model):
    name = models.CharField(max_length=100)  # Tuition, PTA Levy, Uniform, Library Fine, etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="fee_types")
    applies_to_grade = models.CharField(max_length=2, blank=True, help_text="Leave blank to apply to all grades.")

    def __str__(self):
        return f"{self.name} ({self.term}) - D{self.amount}"


class Invoice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    date_issued = models.DateField(auto_now_add=True)

    @property
    def amount_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    @property
    def is_settled(self):
        return self.balance <= 0

    def __str__(self):
        return f"Invoice #{self.id} - {self.student} - {self.fee_type}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK = "BANK", "Bank Transfer"
        MOBILE = "MOBILE", "Mobile Money"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=30, unique=True)
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt {self.receipt_number} - D{self.amount}"
