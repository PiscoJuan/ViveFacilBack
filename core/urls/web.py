from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.api.web.urls')),
    path('catalog/', include('catalog.api.web.urls')),
    path('content/', include('content.api.web.urls')),
    path('payments/', include('payments.api.web.urls')),
    path('promotions/', include('promotions.api.web.urls')),
]
