from django.urls import path
from .views import generate_summary, get_summary, get_generations
urlpatterns = [
    path("get-generations/", get_generations, name="summary-get-generations"),
    path("generate/", generate_summary, name="generate_summary"),
    path("<id>/", get_summary, name="get_summary"),

]