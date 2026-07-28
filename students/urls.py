from django.urls import path
from . import views

app_name = "students"
urlpatterns = [
    path("apply/", views.apply, name="apply"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/<int:pk>/review/", views.application_review, name="application_review"),
    path("", views.student_list, name="student_list"),
    path("<int:pk>/", views.student_detail, name="student_detail"),
]
