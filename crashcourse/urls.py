from django.urls import path
from .views import generate_crash_course, get_crash_course, get_generations

urlpatterns = [
    path("generate-crash-course/", generate_crash_course, name="generate_crash-course" ),
    path("get-crash-course/", get_crash_course, name="get-crash-course"),
    path("get-generations/", get_generations, name="crash-course-get-generations"),

]