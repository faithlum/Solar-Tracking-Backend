from django.contrib import admin
from django.urls import path, include #new
from . import views
from . import axial_tilt

urlpatterns = [
    path('', views.stream_output),
    path('input_form', axial_tilt.tilt_angle_req),
    path('calibrate', axial_tilt.accelerometerHorz),
    path('sse-close-notification', views.sse_close_notification),
]