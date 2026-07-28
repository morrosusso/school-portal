from django.contrib import admin
from .models import Result, ReportCard, ResultUploadLog


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "ca_score", "exam_score", "total_score", "grade", "is_moderated")
    list_filter = ("term", "subject", "is_moderated")
    search_fields = ("student__student_id", "student__first_name", "student__last_name")


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "average_score", "class_position", "is_published")
    list_filter = ("term", "is_published")
    search_fields = ("student__student_id", "student__first_name", "student__last_name")
    actions = ["publish_report_cards"]

    @admin.action(description="Publish selected report cards (students can then download them)")
    def publish_report_cards(self, request, queryset):
        queryset.update(is_published=True)


@admin.register(ResultUploadLog)
class ResultUploadLogAdmin(admin.ModelAdmin):
    list_display = ("file_name", "uploaded_by", "term", "rows_success", "rows_failed", "uploaded_on")
    list_filter = ("term",)
    readonly_fields = ("uploaded_by", "term", "file_name", "rows_total", "rows_success", "rows_failed", "error_details", "uploaded_on")
