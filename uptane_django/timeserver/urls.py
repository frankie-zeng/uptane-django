from django.urls import path

from . import views

urlpatterns = [
    path('', views.get_signed_time, name='get_signed_time'),
]