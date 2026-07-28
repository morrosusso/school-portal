"""
Root URLconf. Each app owns its own urls.py (kept in the app folder)
and is included here under a clean prefix -- this is what "properly
linked" means in practice: one predictable place to find every route.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("academics/", include("academics.urls")),
    path("assessment/", include("assessment.urls")),
    path("finance/", include("finance.urls")),
    path("library/", include("library_mgmt.urls")),
    path("communication/", include("communication.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
