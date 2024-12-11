from django.urls import path
from .views import generate_questions, get_practice_test, explain_answer, get_generations

urlpatterns = [
    path("generate-test/", generate_questions, name="generate-questions"),
    path("get-practice-test/<id>", get_practice_test, name="practice-test"),
    path("explain-answer/", explain_answer, name="explain-answer"),
    path("get-generations/", get_generations, name="practice-test-get-generations"),

]