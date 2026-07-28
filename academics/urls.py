from django.urls import path
from . import views

app_name = "academics"
urlpatterns = [
    path("timetable/", views.timetable_view, name="timetable"),
]
