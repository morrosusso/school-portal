from django.urls import path
from . import views

app_name = "assessment"
urlpatterns = [
    path("my-report-cards/", views.my_report_cards, name="my_report_cards"),
    path("report-card/<int:pk>/download/", views.download_report_card, name="download_report_card"),
    path("transcript/<int:student_id>/download/", views.download_transcript, name="download_transcript"),
    path("results/<int:class_id>/<int:term_id>/<int:subject_id>/", views.enter_results, name="enter_results"),
    path("results/upload-csv/", views.upload_results_csv, name="upload_results_csv"),
]
