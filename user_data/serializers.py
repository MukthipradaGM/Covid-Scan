from django.urls import path, include
from django.contrib.auth.models import User
from .models import Patient_record
from rest_framework import routers, serializers, viewsets


# Serializers define the API representation.
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient_record
        fields = '__all__'


