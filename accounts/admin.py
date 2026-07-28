from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StaffProfile, ParentProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Extends Django's built-in UserAdmin so the Principal / IT Support
    can create staff, students, and parent logins directly from
    /admin/ without needing a developer.
    """
    list_display = ("username", "first_name", "last_name", "role", "is_admin_permission", "is_active")
    list_filter = ("role", "is_active", "is_admin_permission")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("School Role", {"fields": ("role", "phone_number", "profile_photo", "date_of_birth", "address")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("School Role", {"fields": ("role", "email", "first_name", "last_name")}),
    )
    readonly_fields = ("is_admin_permission",)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "qualification", "department", "is_active_staff")
    list_filter = ("qualification", "department", "is_active_staff")
    search_fields = ("staff_id", "user__first_name", "user__last_name")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "relationship")
    filter_horizontal = ("students",)
