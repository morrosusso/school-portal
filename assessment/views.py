"""
assessment/views.py

Download permission rules (the two explicit requirements):
  * Termly report card -> the student may download ONLY their own,
    and only once staff have marked it is_published=True.
  * Transcript -> ONLY staff whose role grants admin permission
    (request.user.is_admin_permission) may download -- students and
    parents cannot, no matter whose transcript it is.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

import csv
import io

from accounts.models import Role
from academics.models import Subject
from students.models import Student
from .models import Result, ReportCard, ResultUploadLog, Term
from .forms import ResultCSVUploadForm
from .utils import generate_report_card_pdf, generate_transcript_pdf


def _is_admin_permission(user):
    return user.is_authenticated and user.is_admin_permission


def _is_teaching_staff(user):
    return user.is_authenticated and user.role in (
        Role.TEACHER, Role.SENIOR_TEACHER, Role.VICE_PRINCIPAL, Role.PRINCIPAL
    )


@login_required
def my_report_cards(request):
    """A student's own list of report cards, with download links for published ones."""
    if request.user.role != Role.STUDENT:
        messages.error(request, "Only student accounts have report cards here.")
        return redirect("core:dashboard")
    student = request.user.student_profile
    report_cards = ReportCard.objects.filter(student=student).select_related("term")
    return render(request, "assessment/my_report_cards.html", {"report_cards": report_cards, "student": student})


@login_required
def download_report_card(request, pk):
    """
    Students can only download their OWN report card, and only once
    it's published. Staff (teachers and up) can download any
    student's report card for administrative purposes.
    """
    report_card = get_object_or_404(ReportCard, pk=pk)
    user = request.user

    is_owner = (user.role == Role.STUDENT and getattr(user, "student_profile", None) == report_card.student)
    is_parent_of_student = False
    if user.role == Role.PARENT:
        parent_profile = getattr(user, "parent_profile", None)
        is_parent_of_student = parent_profile and report_card.student in parent_profile.students.all()

    if not (is_owner or is_parent_of_student or _is_teaching_staff(user) or user.is_admin_permission):
        raise PermissionDenied("You are not permitted to view this report card.")

    if (is_owner or is_parent_of_student) and not report_card.is_published:
        messages.warning(request, "This term's report card has not been published yet. Please check back later.")
        return redirect("assessment:my_report_cards")

    buffer = generate_report_card_pdf(report_card)
    filename = f"{report_card.student.student_id}_report_{report_card.term}.pdf".replace(" ", "_")
    return FileResponse(buffer, as_attachment=True, filename=filename)


@login_required
@user_passes_test(_is_admin_permission, login_url="core:dashboard")
def download_transcript(request, student_id):
    """
    Transcript download -- restricted to staff with admin permission
    ONLY (Principal, Vice Principals, Senior Teachers, Secretary,
    IT Support). Enforced both by the decorator above and the model
    field accounts.User.is_admin_permission, which is recalculated
    automatically from the user's role every time they're saved.
    """
    student = get_object_or_404(Student, pk=student_id)
    buffer = generate_transcript_pdf(student)
    filename = f"{student.student_id}_transcript.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)


@login_required
@user_passes_test(_is_teaching_staff, login_url="core:dashboard")
def upload_results_csv(request):
    """
    Bulk grade upload for teachers -- lets a teacher upload a whole
    class/subject's CA + exam scores in one CSV instead of typing
    them one by one in enter_results().

    Expected header row: student_id, subject_code, ca_score, exam_score

    A plain TEACHER can only upload scores for subjects they are
    actually assigned to teach (checked via TeacherAssignment) --
    this stops one teacher accidentally (or deliberately) overwriting
    another subject's grades. Senior Teachers, Vice Principals and
    the Principal can upload for any subject (moderation/oversight).
    """
    result_rows = None
    log_entry = None

    if request.method == "POST":
        form = ResultCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            term = form.cleaned_data["term"]
            csv_file = form.cleaned_data["csv_file"]

            can_upload_any_subject = request.user.role in (Role.SENIOR_TEACHER, Role.VICE_PRINCIPAL, Role.PRINCIPAL)
            my_subject_codes = set(
                request.user.teaching_assignments.values_list("subject__code", flat=True)
            )

            decoded = io.TextIOWrapper(csv_file.file, encoding="utf-8-sig")
            reader = csv.DictReader(decoded)

            required_columns = {"student_id", "subject_code", "ca_score", "exam_score"}
            if not reader.fieldnames or not required_columns.issubset(set(h.strip() for h in reader.fieldnames)):
                messages.error(
                    request,
                    "CSV header row must contain exactly these columns: student_id, subject_code, ca_score, exam_score"
                )
                return render(request, "assessment/upload_results_csv.html", {"form": form})

            result_rows = []
            success_count = 0
            error_lines = []

            for line_number, row in enumerate(reader, start=2):  # header is line 1
                student_id = (row.get("student_id") or "").strip()
                subject_code = (row.get("subject_code") or "").strip()
                ca_raw = (row.get("ca_score") or "").strip()
                exam_raw = (row.get("exam_score") or "").strip()

                row_report = {"line": line_number, "student_id": student_id, "subject_code": subject_code, "status": "", "detail": ""}

                if not student_id or not subject_code:
                    row_report["status"] = "failed"
                    row_report["detail"] = "Missing student_id or subject_code."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: missing student_id or subject_code")
                    continue

                if not can_upload_any_subject and subject_code not in my_subject_codes:
                    row_report["status"] = "failed"
                    row_report["detail"] = "You are not assigned to teach this subject."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: not authorized for subject {subject_code}")
                    continue

                student = Student.objects.filter(student_id__iexact=student_id).first()
                if not student:
                    row_report["status"] = "failed"
                    row_report["detail"] = "No student found with this Student ID."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: unknown student_id {student_id}")
                    continue

                subject = Subject.objects.filter(code__iexact=subject_code).first()
                if not subject:
                    row_report["status"] = "failed"
                    row_report["detail"] = "No subject found with this subject code."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: unknown subject_code {subject_code}")
                    continue

                if not student.current_class:
                    row_report["status"] = "failed"
                    row_report["detail"] = "Student has no class assigned yet."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: {student_id} has no current class")
                    continue

                try:
                    ca_score = float(ca_raw) if ca_raw != "" else 0
                    exam_score = float(exam_raw) if exam_raw != "" else 0
                    if not (0 <= ca_score <= 40) or not (0 <= exam_score <= 60):
                        raise ValueError("out of range")
                except ValueError:
                    row_report["status"] = "failed"
                    row_report["detail"] = "ca_score must be 0-40 and exam_score must be 0-60."
                    result_rows.append(row_report)
                    error_lines.append(f"Line {line_number}: invalid score(s) for {student_id}")
                    continue

                Result.objects.update_or_create(
                    student=student, subject=subject, term=term,
                    defaults={
                        "school_class": student.current_class,
                        "ca_score": ca_score,
                        "exam_score": exam_score,
                        "entered_by": request.user,
                    }
                )
                row_report["status"] = "success"
                row_report["detail"] = f"Saved: CA {ca_score}, Exam {exam_score}"
                result_rows.append(row_report)
                success_count += 1

            log_entry = ResultUploadLog.objects.create(
                uploaded_by=request.user,
                term=term,
                file_name=csv_file.name,
                rows_total=len(result_rows),
                rows_success=success_count,
                rows_failed=len(result_rows) - success_count,
                error_details="\n".join(error_lines),
            )

            if success_count:
                messages.success(request, f"{success_count} of {len(result_rows)} rows saved successfully.")
            if log_entry.rows_failed:
                messages.warning(request, f"{log_entry.rows_failed} row(s) failed -- see details below.")
    else:
        form = ResultCSVUploadForm()

    return render(request, "assessment/upload_results_csv.html", {
        "form": form, "result_rows": result_rows, "log_entry": log_entry,
    })


@login_required
@user_passes_test(_is_teaching_staff, login_url="core:dashboard")
def enter_results(request, class_id, term_id, subject_id):
    """Bulk score-entry screen for a teacher's class/subject/term."""
    from academics.models import SchoolClass, Subject
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    students = Student.objects.filter(current_class=school_class, is_active=True)

    if request.method == "POST":
        for student in students:
            ca = request.POST.get(f"ca_{student.id}")
            exam = request.POST.get(f"exam_{student.id}")
            if ca is None and exam is None:
                continue
            Result.objects.update_or_create(
                student=student, subject=subject, term=term,
                defaults={
                    "school_class": school_class,
                    "ca_score": ca or 0,
                    "exam_score": exam or 0,
                    "entered_by": request.user,
                }
            )
        messages.success(request, "Scores saved.")
        return redirect("assessment:enter_results", class_id=class_id, term_id=term_id, subject_id=subject_id)

    existing = {r.student_id: r for r in Result.objects.filter(school_class=school_class, term=term, subject=subject)}
    # Attach each student's existing result (if any) directly onto the
    # object so the template can do a simple {{ s.existing_result.ca_score }}
    # instead of a dict lookup (Django templates can't index a dict by a
    # loop variable without a custom filter).
    for s in students:
        s.existing_result = existing.get(s.id)

    return render(request, "assessment/enter_results.html", {
        "school_class": school_class, "term": term, "subject": subject,
        "students": students,
    })
