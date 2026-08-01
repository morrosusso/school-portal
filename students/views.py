"""
students/views.py

Applicant flow (public, no staff involved):
  1. apply() -- signup: name, email, password, gender -> creates a
     login account with role=APPLICANT.
  2. applicant_dashboard() -- once logged in: complete the full
     application details, upload supporting documents, track status,
     download a PDF summary.
Then staff review/accept workflow, and student/staff-facing lists.
"""

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import FileResponse
from django.contrib.auth import get_user_model

from accounts.models import Role
from .forms import ApplicationForm, ApplicationReviewForm, StudentClassAssignForm, ApplicantSignupForm, ApplicantDocumentForm
from .models import Application, Student, ApplicantDocument
from .utils import generate_application_summary_pdf

User = get_user_model()


def apply(request):
    """
    Step 1 of the applicant flow -- create a login account (full
    name, email, password, gender). No admission details are
    collected here; those are filled in on the Applicant Dashboard
    right after signing up.
    """
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = ApplicantSignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=Role.APPLICANT,
            )
            Application.objects.create(
                user=user,
                first_name=data["first_name"],
                last_name=data["last_name"],
                gender=data["gender"],
            )
            auth_login(request, user)
            messages.success(request, "Account created! Please complete your application details below.")
            return redirect("students:applicant_dashboard")
    else:
        form = ApplicantSignupForm()
    return render(request, "students/apply.html", {"form": form})


@login_required
def applicant_dashboard(request):
    """
    The applicant's home base: complete application details (if not
    done yet), upload supporting documents, see their status, and
    download a PDF summary at any point.
    """
    if request.user.role != Role.APPLICANT:
        return redirect("core:dashboard")

    application = getattr(request.user, "applicant_application", None)
    if application is None:
        # Shouldn't normally happen (created at signup), but handle
        # gracefully rather than erroring out.
        application = Application.objects.create(
            user=request.user, first_name=request.user.first_name,
            last_name=request.user.last_name, gender=Application.Gender.MALE
        )

    application_form = None
    document_form = None

    if request.method == "POST" and "submit_application" in request.POST:
        application_form = ApplicationForm(request.POST, request.FILES, instance=application)
        if application_form.is_valid():
            application = application_form.save(commit=False)
            application.is_submitted = True
            application.save()
            messages.success(request, "Application details submitted! The school office will review it soon.")
            return redirect("students:applicant_dashboard")
    elif not application.is_submitted:
        application_form = ApplicationForm(instance=application)

    if request.method == "POST" and "upload_document" in request.POST:
        document_form = ApplicantDocumentForm(request.POST, request.FILES)
        if document_form.is_valid():
            doc = document_form.save(commit=False)
            doc.application = application
            doc.save()
            messages.success(request, "Document uploaded.")
            return redirect("students:applicant_dashboard")
    else:
        document_form = ApplicantDocumentForm()

    return render(request, "students/applicant_dashboard.html", {
        "application": application,
        "application_form": application_form,
        "document_form": document_form,
        "documents": application.documents.all() if application.pk else [],
    })


@login_required
def delete_document(request, pk):
    document = get_object_or_404(ApplicantDocument, pk=pk)
    if document.application.user_id != request.user.id:
        messages.error(request, "You may only remove your own documents.")
        return redirect("students:applicant_dashboard")
    document.delete()
    messages.success(request, "Document removed.")
    return redirect("students:applicant_dashboard")


@login_required
def download_application_summary(request, pk):
    application = get_object_or_404(Application, pk=pk)
    is_owner = application.user_id == request.user.id
    is_staff_reviewer = request.user.is_authenticated and request.user.role in (
        Role.PRINCIPAL, Role.VICE_PRINCIPAL, Role.SECRETARY, Role.IT_SUPPORT
    )
    if not (is_owner or is_staff_reviewer):
        messages.error(request, "You are not permitted to view this application.")
        return redirect("core:dashboard")

    buffer = generate_application_summary_pdf(application)
    filename = f"application_{application.id}_summary.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)


def _is_admissions_staff(user):
    return user.is_authenticated and user.role in (Role.PRINCIPAL, Role.VICE_PRINCIPAL, Role.SECRETARY, Role.IT_SUPPORT)


@login_required
@user_passes_test(_is_admissions_staff, login_url="core:dashboard")
def application_list(request):
    status_filter = request.GET.get("status", "")
    applications = Application.objects.filter(is_submitted=True)
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
@user_passes_test(_is_admissions_staff, login_url="core:dashboard")
def reset_student_password(request, pk):
    """
    Lets admin-permission staff (Principal, VPs, Secretary, IT
    Support) reset a student's forgotten password directly from the
    portal, without needing to go into /admin/. Resets it back to
    their Student ID -- the same simple, memorable scheme used when
    their account was first created -- and the student can change it
    again from their profile afterwards.
    """
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        if not student.user:
            messages.error(request, "This student has no login account to reset.")
            return redirect("students:student_detail", pk=pk)
        student.user.set_password(student.student_id)
        student.user.save()
        messages.success(request, f"Password reset for {student} -- new password is their Student ID ({student.student_id}).")
    return redirect("students:student_detail", pk=pk)


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
