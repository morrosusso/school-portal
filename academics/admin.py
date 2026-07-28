from django.contrib import admin
from .models import Department, Subject, AcademicSession, Term, SchoolClass, TeacherAssignment, TimetableSlot


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "head_of_department")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "is_core")
    list_filter = ("department", "is_core")
    search_fields = ("name", "code")


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_current")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("session", "name", "is_current", "start_date", "end_date")
    list_filter = ("session",)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("label", "grade", "stream", "class_teacher")
    list_filter = ("grade",)
    filter_horizontal = ("subjects",)


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "subject", "school_class")
    list_filter = ("school_class", "subject")


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ("school_class", "subject", "teacher", "day", "period", "room")
    list_filter = ("school_class", "day")
