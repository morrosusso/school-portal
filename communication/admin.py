from django.contrib import admin
from .models import Notice, DirectMessage


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "posted_by", "posted_on", "pinned")
    list_filter = ("audience", "pinned")


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "sent_on", "is_read")
