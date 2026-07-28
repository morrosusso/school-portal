from django.urls import path
from . import views

app_name = "communication"
urlpatterns = [
    path("notices/", views.notice_board, name="notice_board"),
]
