"""
core/views.py

home()      -- public landing page (links to Apply + Login).
dashboard() -- single entry point after login; renders a different
               template per role so every user category from the
               blueprint gets a relevant dashboard, while keeping
               ONE view/URL to maintain (`core:dashboard`).
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.models import Role
from students.models import Application, Student
from assessment.models import ReportCard
from finance.models import Invoice
from communication.models import Notice
from library_mgmt.models import BorrowRecord


def home(request):
    if request.user.is_authenticated:
        return render(request, "core/home.html")
    return render(request, "core/home.html")


ROLE_TEMPLATES = {
    Role.PRINCIPAL: "core/dashboards/principal.html",
    Role.VICE_PRINCIPAL: "core/dashboards/vice_principal.html",
    Role.SENIOR_TEACHER: "core/dashboards/teacher.html",
    Role.TEACHER: "core/dashboards/teacher.html",
    Role.BURSAR: "core/dashboards/bursar.html",
    Role.SECRETARY: "core/dashboards/secretary.html",
    Role.IT_SUPPORT: "core/dashboards/it_support.html",
    Role.LIBRARIAN: "core/dashboards/librarian.html",
    Role.NON_TEACHING: "core/dashboards/non_teaching.html",
    Role.PARENT: "core/dashboards/parent.html",
    Role.STUDENT: "core/dashboards/student.html",
    Role.CLUSTER_MONITOR: "core/dashboards/cluster_monitor.html",
}


@login_required
def dashboard(request):
    user = request.user
    if user.role == Role.APPLICANT:
        return redirect("students:applicant_dashboard")

    template = ROLE_TEMPLATES.get(user.role, "core/dashboards/generic.html")
    context = {"recent_notices": [n for n in Notice.objects.all()[:5] if n.visible_to(user)]}

    if user.role == Role.PRINCIPAL or user.role == Role.VICE_PRINCIPAL:
        context.update({
            "total_students": Student.objects.filter(is_active=True).count(),
            "pending_applications": Application.objects.filter(status=Application.Status.PENDING).count(),
            "outstanding_fees": sum(i.balance for i in Invoice.objects.all()),
        })
    elif user.role == Role.SECRETARY:
        context["pending_applications"] = Application.objects.filter(status=Application.Status.PENDING).count()
    elif user.role in (Role.TEACHER, Role.SENIOR_TEACHER):
        context["my_assignments"] = user.teaching_assignments.select_related("subject", "school_class")
    elif user.role == Role.BURSAR:
        context["outstanding_fees"] = sum(i.balance for i in Invoice.objects.all())
    elif user.role == Role.STUDENT:
        student = getattr(user, "student_profile", None)
        context["student"] = student
        if student:
            context["report_cards"] = ReportCard.objects.filter(student=student, is_published=True)
    elif user.role == Role.PARENT:
        parent_profile = getattr(user, "parent_profile", None)
        context["children"] = parent_profile.students.all() if parent_profile else []
    elif user.role == Role.LIBRARIAN:
        context["overdue_count"] = BorrowRecord.objects.filter(returned_on__isnull=True).count()

    return render(request, template, context)
