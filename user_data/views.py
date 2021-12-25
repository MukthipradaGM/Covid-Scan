from django.http.response import HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PatientForm
from .models import Patient_record
import uuid
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
import tensorflow as tf
import pandas as pd
import random
from imutils import paths
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import preprocessing
import cv2
import os
from tensorflow import keras 
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import sys
from PIL import Image
import urllib.request as ur
import requests
from google.cloud import storage
from rest_framework import routers, serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view ,permission_classes
from user_data.serializers import PatientSerializer
from rest_framework import permissions
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
from twilio.rest import Client
from io import StringIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from html import escape
from io import BytesIO
import pdfkit
import datetime
import wkhtmltopdf

current_date = datetime.datetime.now()
os.environ["CUDA_VISIBLE_DEVICES"]="-1" 
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=os.path.join(BASE_DIR,'credentials.json')

# Please mention path to your h5 file
# Place your h5 file inside the model folder
model_path = os.path.join(BASE_DIR,'models\lenet\lenet.h5')


model = tf.keras.models.load_model(model_path)
bucket_name = "GCP BUCKET NAME" #Enter GCP BUCKET NAME
storage_client = storage.Client()


#Downloading File From GCP Bucket
def download_file_from_bucket(blob_name,file_path,bucket_name):
    try:
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        with open(file_path,'wb') as f:
            storage_client.download_blob_to_file(blob,f)
        return True
    except Exception as e:
        print(e)
        return False

#Model Output
def model_output(img_name):
    x = download_file_from_bucket('Xray/'+img_name,os.path.join(BASE_DIR,'media/'+img_name),bucket_name)
    img_path = os.path.join(BASE_DIR,'media\\'+img_name) 
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img,(299,299))
    x = img_to_array(img)
    x = x.reshape((1,) + x.shape)
    x /= 255
    successive_maps = model(x)
    temp = np.argmax(successive_maps,axis=-1)
    temp1 = temp.astype(int)
    disease_type = str(temp1[0])
    probability = np.max(successive_maps,axis=-1)[0]
    final_res = save_result(disease_type,probability)
    os.remove(img_path)
    return final_res

#Categorizing Model's Output Based On Severity Scale
def save_result(disease_type,probability):
    severity = ["MILD","MODERATE","SEVERE"]
    result = ["POSITIVE","NEGATIVE"]
    if disease_type == '0':
        if probability > 0.5 and probability < 0.70:
            status = severity[0]
            percentage = "{:.2%}".format(probability)
            prob_val = percentage
            res = result[0]
        elif probability > 0.7 and probability < 0.80:
            status = severity[1]
            percentage = "{:.2%}".format(probability)
            prob_val = percentage
            res = result[0]
        elif probability > 0.8 and probability < 1.0:
            status = severity[2]
            percentage = "{:.2%}".format(probability)
            prob_val = percentage
            res = result[0]
    else:
        status = "UNINFECTED"
        prob_val1 = 1 - probability
        percentage = "{:.2%}".format(prob_val1)
        prob_val = percentage
        res =result[1]
    
    final_res = [status,prob_val,res]
    
    return final_res

#Send reference Id to patient
def send_ref_id_email(ref_id,email):
    subject = 'Your Reference Number is Here...'
    message = 'Your Reference Number is '+ref_id+'--From Team CovidScan'
    to_email = [email]
    from_email = settings.EMAIL_HOST_USER
    email = EmailMessage(subject,message,from_email,to_email)
    email.send()
    return "Success"

#Send Scan Result to patient
def send_result_email(ref_id,result,email):
    subject = 'Your Result is Here...'
    message = 'Your Result is '+result+'--From Team CovidScan'
    to_email = [email]
    from_email = settings.EMAIL_HOST_USER
    email = EmailMessage(subject,message,from_email,to_email)
    email.send()
    return "Success"  

#Add New Patient Record
@login_required
def addnew(request):
    form =PatientForm(request.POST,request.FILES)
    if request.method == 'POST' and form.is_valid():
        doc=form.save(commit=False)
        #Add ref_id
        name =  form.cleaned_data['Patient_Name']
        age =  form.cleaned_data['Patient_Age']
        gender =  form.cleaned_data['Patient_Gender']
        email = form.cleaned_data['Patient_Email']
        mobile = form.cleaned_data['Patient_Mobile']
        address = form.cleaned_data['Patient_Address']
        aadhar = form.cleaned_data['Patient_Aadharnumber']
        unique_id = Patient_record.get_ref_id()
        new_name = unique_id+".jpg"
        xray   = form.cleaned_data['x_rayimage']
        xray.name = new_name
        new_join,created = Patient_record.objects.get_or_create(Patient_Name= name,
                                                                Patient_Age= age,
                                                                Patient_Gender= gender,
                                                                Patient_Email = email,
                                                                Patient_Mobile = mobile,
                                                                Patient_Address = address,
                                                                Patient_Aadharnumber = aadhar,
                                                                x_rayimage = xray,
                                                                Scan_time = current_date,
                                                                )
        
        if created:
            
            new_join.Patient_Ref_id = unique_id
            new_join.save()
            img_name = xray.name 
            output = model_output(img_name)
            new_join.Patient_Status = output[0]
            new_join.Patient_Severity = output[1]
            new_join.Patient_Result = output[2]
            new_join.save()
            send_ref_id_email(unique_id,email)
            send_result_email(unique_id,output[2],email)
            return redirect('index')
    else:
        form = PatientForm()

    return render(request,"user_data/addrecord.html",{'form': form})

#Display All Patients list
@login_required
def patient_list(request):
    if request.method == "POST":
        searched = request.POST['searched']
        record_list= Patient_record.objects.filter(Patient_Name__contains=searched) 
        return render(request,'user_data/patient_list.html',
        {'searched' : searched,
        'record_list' : record_list})
    else:
        return render(request,'user_data/patient_list.html',{})

#Generate PDF From HTML
def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = context_dict
    html  = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))

#Generate SCAN REPORT
@login_required
def generate_report(request):
    if request.method == "POST":
        searched = request.POST['searched']
        record_list= Patient_record.objects.filter(Patient_Ref_id=searched) 
        return render(request,'user_data/report.html',
        {'searched' : searched,
        'record_list' : record_list})
    else:
        return render(request,'user_data/report.html',{})

#Download Report In PDF Format
@login_required
def download_report(request):
    if request.method == "POST":
        id = request.POST['ref_id']
        record_list= Patient_record.objects.filter(Patient_Ref_id=id)
        return render_to_pdf(
            'user_data/download_report.html',
            {
                    'record_list' : record_list
            }
           
        ) #Please Comment out above return line if you don't want report in pdf format

        # return render(request,'user_data/download_report.html',{'record_list' : record_list}) # Generate Report IN HTML format
        # result = pdfkit.from_file('C://Projects//capstone_cloud//covid_scan//templates//user_data//download_report.html','result.pdf')
        # return HttpResponse(result.getvalue(), content_type='application/pdf') 
    return render(request,'user_data/download_report.html')




# @login_required
# def start_scan(request):
#     return render(request,'user_data/start_scan.html')


#If You Want Download Report As REST API Please use below function

'''
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def show_record(request):
    if request.method == 'GET':
        ref_id = request.query_params.get('ref_id')
        try:
            results = Patient_record.objects.filter(Patient_Ref_id=ref_id)
            serialze = PatientSerializer(results,many=True)
            return Response(serialze.data)
        except Patient_record.DoesNotExist:
            return HttpResponse('<h1>Not Found</h1>')
'''

#Send Refrence Via Twilio SMS Service

# def send_sms_ref_id(ref_id,mobile_num):
    
#     patient_ref_id = ref_id
#     msg_body = '''Your Reference Number is Here...
#                   Your Reference Number is''' +ref_id+ '''--From Team CovidScan '''
#     # Your Account SID from twilio.com/console
#     account_sid = settings.ACCOUNT_SID
#     # Your Auth Token from twilio.com/console
#     auth_token  = settings.AUTH_TOKEN
#     client = Client(account_sid, auth_token)
#     message = client.messages.create(
#         to=mobile_num, 
#         from_="TWILIO MOBILE NUMBER",
#         body=msg_body)
#     return 0

#Send Result Via Twilio SMS Service

# def send_sms_result(ref_id,mobile_num):
#     patient_ref_id = ref_id
#     msg_body = '''Your Reference Number is Here...
#                   Your Reference Number is''' +ref_id+ '''--From Team CovidScan '''
#     # Your Account SID from twilio.com/console
#     account_sid = settings.ACCOUNT_SID
#     # Your Auth Token from twilio.com/console
#     auth_token  = settings.AUTH_TOKEN
#     client = Client(account_sid, auth_token)
#     message = client.messages.create(
#         to=mobile_num, 
#         from_="Twilio Phone Number",
#         body=msg_body)
#     return 0
