from django.urls import path
from . import views

app_name = "students"
urlpatterns = [
    path("apply/", views.apply, name="apply"),
    path("my-application/", views.applicant_dashboard, name="applicant_dashboard"),
    path("my-application/documents/<int:pk>/delete/", views.delete_document, name="delete_document"),
    path("applications/<int:pk>/summary-pdf/", views.download_application_summary, name="download_application_summary"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/<int:pk>/review/", views.application_review, name="application_review"),
    path("", views.student_list, name="student_list"),
    path("<int:pk>/", views.student_detail, name="student_detail"),
    path("<int:pk>/reset-password/", views.reset_student_password, name="reset_student_password"),
]
