from django.urls import path
from .views import chat, get_thread

urlpatterns = [
     path("", chat, name="chat"),
     path("get-thread/", get_thread, name="get_thread"),
]