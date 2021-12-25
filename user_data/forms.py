from django import forms
from django.db import models
from .models import Patient_record
from django.forms import ModelForm


class PatientForm(forms.ModelForm):
    class Meta:
        model  = Patient_record
        fields = ('Patient_Name','Patient_Age','Patient_Gender','Patient_Mobile', 'Patient_Email','Patient_Address','Patient_Aadharnumber','x_rayimage')
         
         
       
         
         
         