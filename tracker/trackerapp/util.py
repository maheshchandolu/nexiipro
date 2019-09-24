
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from trackerapp.models import User,Projects,ProjectVersions,ProjectUsers
from rest_framework import response, status
import requests, urllib, datetime, os, webbrowser
from django.conf import settings
from trackerapp import templates
from django.template import loader



# creates SMTP session 
def send(mail,url):
    '''
        It sends an email for Sign-up verification
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("signup.html")
    response= template.render(url)
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Sign-up Activation"
    message.attach(part2)
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()

def invite(mail,url):
    '''
        It is for Sign-up verification if user invited to project and he/she doesn't exists 
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("invite_signup.html")
    response= template.render(url)
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Invitation To Project"
    message.attach(part2)
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()

def project_invite(mail,url):
    '''
        It is for If User Exists in App and Invite To A Project 
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("invite_user.html")
    response= template.render(url)
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Invitation To Project"
    message.attach(part2)
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()

def profile_update(mail,url):
    '''
        It is For Profile Update
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("user_update.html")
    response= template.render(url)
    # part1= MIMEText(text,'plain')
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Profile Updated"
    # message.attach(part1)
    message.attach(part2)
    # message = 'Subject: {}\n'.format("Forget password")
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()



def password_update(mail,url):
    '''
        It is For Profile Update
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("password_update.html")
    response= template.render(url)
    # part1= MIMEText(text,'plain')
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Password Updated"
    # message.attach(part1)
    message.attach(part2)
    # message = 'Subject: {}\n'.format("Forget password")
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()

def forgot(mail,url):
    '''
        It sends an email for forgotpassword
    '''
    link=smtplib.SMTP('smtp.gmail.com',587)
    link.starttls()
    template= loader.get_template("forgot.html")
    response= template.render(url)
    part2= MIMEText(response,'html')
    message= MIMEMultipart('alternative')
    message["Subject"] = "Forget Password"
    message.attach(part2)
    link.login(settings.USEREMAIL,settings.PASSWORD)
    link.sendmail(settings.USEREMAIL,mail,message.as_string())
    link.quit()


def auth(func):
    """
        Allows The User BY Authenticating 
    """
    def wrap(request, *args, **kwargs):

        if 'Authorization' in request.headers:      
            access_token= request.headers['Authorization'].split('Bearer')[1].strip()
            session= User.objects.filter(reset_code=access_token)
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
            session= User.objects.filter(reset_code=access_token)
            if session.count():
                request.auth= session[0]
            else:
                return response.Response({'message':"Please Re-Login"}, status=status.HTTP_401_UNAUTHORIZED)
        return func(cls, request, *args, **kwargs)


    wrap.__doc__= func.__doc__
    wrap.__name__= func.__name__
    return wrap