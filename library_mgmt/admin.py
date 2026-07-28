from django.contrib import admin
from .models import Book, BorrowRecord


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "total_copies", "copies_available")
    search_fields = ("title", "author", "isbn")


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("book", "student", "borrowed_on", "due_date", "returned_on", "is_overdue")
    list_filter = ("returned_on",)
    search_fields = ("book__title", "student__student_id")
