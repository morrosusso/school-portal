from django.contrib import admin
from .models import FeeType, Invoice, Payment


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "term", "amount", "applies_to_grade")
    list_filter = ("term",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("date_paid",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "fee_type", "amount_due", "amount_paid", "balance", "is_settled")
    list_filter = ("fee_type__term",)
    search_fields = ("student__student_id", "student__first_name", "student__last_name")
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "invoice", "amount", "method", "date_paid")
    list_filter = ("method",)
    search_fields = ("receipt_number",)
