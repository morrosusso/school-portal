from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from accounts.models import Role
from students.models import Student
from .models import Invoice


def _is_bursar_or_above(user):
    return user.is_authenticated and user.role in (Role.BURSAR, Role.PRINCIPAL, Role.VICE_PRINCIPAL)


@login_required
@user_passes_test(_is_bursar_or_above, login_url="core:dashboard")
def finance_overview(request):
    invoices = Invoice.objects.select_related("student", "fee_type").all()
    total_due = sum(i.amount_due for i in invoices)
    total_paid = sum(i.amount_paid for i in invoices)
    return render(request, "finance/overview.html", {
        "invoices": invoices, "total_due": total_due, "total_paid": total_paid,
        "outstanding": total_due - total_paid,
    })


@login_required
def my_fee_balance(request):
    """Students/parents check their own fee balance -- read-only."""
    student = None
    if request.user.role == Role.STUDENT:
        student = getattr(request.user, "student_profile", None)
    invoices = Invoice.objects.filter(student=student) if student else []
    return render(request, "finance/my_balance.html", {"invoices": invoices, "student": student})
