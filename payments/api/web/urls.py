from django.urls import path

from payments.api.web.views import BancosWebView

urlpatterns = [
    path("bancos/", BancosWebView.as_view()),
]
