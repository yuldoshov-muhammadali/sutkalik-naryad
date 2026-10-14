from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("naryad.urls")),
]

handler403 = "naryad.views.permission_denied"
