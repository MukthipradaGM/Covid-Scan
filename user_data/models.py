from django.db import models
from PIL import Image
import uuid
import datetime
current_date = datetime.datetime.now()

# Create your models here.
class Patient_record(models.Model):

    Patient_Name            =models.CharField(max_length=150)
    Patient_Age             =models.CharField(max_length=3,default="18")
    Patient_Gender          =models.CharField(max_length=7,default="")
    Patient_Mobile          =models.CharField(max_length=12)
    Patient_Email           =models.EmailField(max_length=150,blank=True)
    Patient_Address         =models.TextField(max_length=250)
    Patient_Aadharnumber    =models.CharField(max_length=13)
    Patient_Ref_id          =models.CharField(max_length=12, default="ABC", unique=True)
    x_rayimage              =models.ImageField(default="",upload_to='Xray')
    Patient_Status          =models.CharField(max_length=10,default="NA")
    Patient_Severity        =models.CharField(max_length=50,default="NA")
    Patient_Result          =models.CharField(max_length=25,default="NA")
    Scan_time               =models.DateTimeField(default=current_date)

    def __str__(self):
        return self.Patient_Name

    # Generate Unique ID for all patients
    def get_ref_id():
        ref_id = str(uuid.uuid4())[:12].replace('-','').upper()
        try:
            id_exists = Patient_record.obects.get(Patient_Ref_id = Patient_Ref_id)
            get_ref_id()
        except:
            return ref_id









