"""
students/views.py

Public application submission + staff review/accept workflow +
student/staff-facing lists.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from accounts.models import Role
from .forms import ApplicationForm, ApplicationReviewForm, StudentClassAssignForm
from .models import Application, Student


def apply(request):
    """Public admission form -- anyone can access this, no login needed."""
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            messages.success(
                request,
                f"Application submitted successfully! Your reference number is #{application.id}. "
                "The school office will contact your guardian once it has been reviewed."
            )
            return redirect("students:apply")
    else:
        form = ApplicationForm()
    return render(request, "students/apply.html", {"form": form})


def _is_admissions_staff(user):
    return user.is_authenticated and user.role in (Role.PRINCIPAL, Role.VICE_PRINCIPAL, Role.SECRETARY, Role.IT_SUPPORT)


@login_required
@user_passes_test(_is_admissions_staff, login_url="core:dashboard")
def application_list(request):
    status_filter = request.GET.get("status", "")
    applications = Application.objects.all()
    if status_filter:
        applications = applications.filter(status=status_filter)
    paginator = Paginator(applications, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "students/application_list.html", {
        "page_obj": page_obj, "status_filter": status_filter, "statuses": Application.Status.choices
    })


@login_required
@user_passes_test(_is_admissions_staff, login_url="core:dashboard")
def application_review(request, pk):
    """
    Changing status to ACCEPTED here triggers the pre_save signal in
    signals.py, which auto-creates the Student record + student ID +
    login account -- no extra code needed here.
    """
    application = get_object_or_404(Application, pk=pk)
    if request.method == "POST":
        form = ApplicationReviewForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            application.reviewed_by = request.user
            application.save()
            if application.status == Application.Status.ACCEPTED:
                student = getattr(application, "student_record", None)
                if student:
                    messages.success(request, f"Application accepted. Student ID {student.student_id} generated automatically.")
            else:
                messages.info(request, "Application status updated.")
            return redirect("students:application_list")
    else:
        form = ApplicationReviewForm(instance=application)
    return render(request, "students/application_review.html", {"form": form, "application": application})


@login_required
def student_list(request):
    """Visible to staff. Teachers see only their assigned classes' students (kept simple: all staff see all for now)."""
    students = Student.objects.filter(is_active=True)
    class_filter = request.GET.get("class_id")
    if class_filter:
        students = students.filter(current_class_id=class_filter)
    paginator = Paginator(students, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    from academics.models import SchoolClass
    return render(request, "students/student_list.html", {
        "page_obj": page_obj, "school_classes": SchoolClass.objects.all(), "class_filter": class_filter
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    # Students/parents may only view their own record.
    if request.user.role == Role.STUDENT and getattr(request.user, "student_profile", None) != student:
        messages.error(request, "You may only view your own student record.")
        return redirect("core:dashboard")
    if request.user.role == Role.PARENT:
        parent_profile = getattr(request.user, "parent_profile", None)
        if not parent_profile or student not in parent_profile.students.all():
            messages.error(request, "You may only view your own child's record.")
            return redirect("core:dashboard")

    assign_form = None
    if _is_admissions_staff(request.user) and request.method == "POST":
        assign_form = StudentClassAssignForm(request.POST, instance=student)
        if assign_form.is_valid():
            assign_form.save()
            messages.success(request, "Class assignment updated.")
            return redirect("students:student_detail", pk=pk)
    elif _is_admissions_staff(request.user):
        assign_form = StudentClassAssignForm(instance=student)

    return render(request, "students/student_detail.html", {"student": student, "assign_form": assign_form})
