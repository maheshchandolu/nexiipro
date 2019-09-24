
import smtplib 
from nexiiapp.models import User,UserType,UserSecret,UserToken,Requirement,Upload,UserCredit,TransactionHistory,AccountDetails
from rest_framework import response, status
import random
from django.conf import settings
import requests, urllib, datetime, os, webbrowser
from django.core.files.storage import FileSystemStorage
from os.path import splitext
from datetime import datetime

# creates SMTP session 
def send(mail,url):
    '''
        It sends an email for verification
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    message = 'Subject: {}\n\n{}'.format("Welcome to CV Bank", str("Please Signup By Clicking Link - "+str(url)))
    link.login("unifiedsimplified.automation@gmail.com","mypassword@2")
    link.sendmail("unifiedsimplified.automation@gmail.com",mail,message)
    link.quit()


def forgot(mail,url):
    '''
        It sends an email for verification
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    message = 'Subject: {}\n\n{}'.format("Forget password",str("Please Click Link To Change Password - "+str(url)))
    link.login("unifiedsimplified.automation@gmail.com","mypassword@2")
    link.sendmail("unifiedsimplified.automation@gmail.com",mail,message)
    link.quit()


def auth(func):
    """
        Allows The User BY Authenticating 
    """

    def wrap(request, *args, **kwargs):
        # access_token= request.headers.Authorization['access_token'] if 'access_token' in request.headers.Authorization \
                                # else ''

        # if 'temp_auth_id' in request.data and request.data['temp_auth_id']:
        #     session= User.objects.filter(user_name = request.data['temp_auth_id'])                
        #     if session.count():
        #         request.auth= session[0]
        #         return func(request, *args, **kwargs)
        #     else:
        #         session= User.objects.create(user_name = request.data['temp_auth_id'])
        #         request.auth= session
        #         return func(request, *args, **kwargs)


        # else:
        if 'Authorization' in request.headers:      
            access_token= request.headers['Authorization'].split('Bearer')[1].strip()
            session= UserSecret.objects.filter(reset_code=access_token)
            if session.count():
                request.auth= session[0]
            else:
                return response.Response({'message':"Please Re-Login"}, status=status.HTTP_401_UNAUTHORIZED)
            return func(request, *args, **kwargs)

    wrap.__doc__= func.__doc__
    wrap.__name__= func.__name__
    return wrap

def auth_cls(func):
    """
        Allows The User BY Authenticating 
    """
    
    def wrap(cls, request, *args, **kwargs):
        
        if 'Authorization' in request.headers:      
            access_token= request.headers['Authorization'].split('Bearer')[1].strip()
            session= UserSecret.objects.filter(reset_code=access_token)
            if session.count():
                request.auth= session[0]
            else:
                return response.Response({'message':"Please Re-Login"}, status=status.HTTP_401_UNAUTHORIZED)
            return func(cls, request, *args, **kwargs)


    wrap.__doc__= func.__doc__
    wrap.__name__= func.__name__
    return wrap



def save(uploaded_file):
    fs=FileSystemStorage()
    data= fs.save(
        uploaded_file.name,
        uploaded_file
    )
    return True



def file_path(uploaded_file):
    return settings.MEDIA_ROOT+'/'+str(uploaded_file)

def file_size(uploaded_file):
    return os.path.getsize(settings.MEDIA_ROOT+'/'+str(uploaded_file))

def file_name(uploaded_file):
    file_name = (uploaded_file.split('/')[-1]).split('.')[0]
    return file_name

def file_extension(uploaded_file):
    file_extension = uploaded_file.split('/')[-1].split('.')[-1]
    return file_extension

def assigned_name():
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    date_time = datetime.fromtimestamp(timestamp)
    assigned_name = date_time.strftime("%c")
    return assigned_name


