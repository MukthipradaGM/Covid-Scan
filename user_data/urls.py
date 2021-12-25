from django.urls import path
from . import views

urlpatterns = [
    path('addnew', views.addnew,name='addnew'),
    path('patient_list', views.patient_list,name='patient_list'),
    path('start_scan', views.start_scan,name='start_scan'),
    # path('show_record', views.show_record,name='show_record'),
    path('generate_report', views.generate_report,name='generate_report'),
    path('download_report', views.download_report,name='download_report'),
]