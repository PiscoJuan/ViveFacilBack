from django.urls import re_path

from api.views import AdminPage

urlpatterns = [
    re_path("static/", AdminPage.as_view()),
]
