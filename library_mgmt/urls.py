from django.urls import path
from . import views

app_name = "library_mgmt"
urlpatterns = [
    path("catalog/", views.catalog, name="catalog"),
    path("my-books/", views.my_borrowed_books, name="my_books"),
]
