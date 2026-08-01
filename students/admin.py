from django.contrib import admin
from .models import Application, Student, DisciplineRecord, AttendanceRecord, ApplicantDocument


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "applying_for_grade", "is_submitted", "status", "submitted_on")
    list_filter = ("status", "is_submitted", "applying_for_grade")
    search_fields = ("first_name", "last_name", "guardian_name", "guardian_phone", "user__email")
    readonly_fields = ("submitted_on", "reviewed_on", "user")
    # Changing status here to ACCEPTED also auto-creates (or converts
    # the applicant's existing account into) the Student record via
    # the pre_save signal in signals.py.


@admin.register(ApplicantDocument)
class ApplicantDocumentAdmin(admin.ModelAdmin):
    list_display = ("label", "application", "uploaded_on")
    search_fields = ("label", "application__first_name", "application__last_name")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "first_name", "last_name", "current_class", "is_active")
    list_filter = ("current_class", "is_active")
    search_fields = ("student_id", "first_name", "last_name")
    readonly_fields = ("student_id", "date_admitted")


@admin.register(DisciplineRecord)
class DisciplineRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "action_taken")
    list_filter = ("date",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status")
    list_filter = ("status", "date")
