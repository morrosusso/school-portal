from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("overview/", views.finance_overview, name="overview"),
    path("my-balance/", views.my_fee_balance, name="my_balance"),
]
