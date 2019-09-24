from django.shortcuts import render
import secrets, os, validators
from . import models
from trackerapp.models import User,Projects,ProjectVersions,ProjectUsers
from rest_framework import viewsets, response, decorators, status
from . serializers import UserSerializer,UserResponseSerializer,UserVersionsSerializer, ProjectsSerializer,ProjectsNameSerializer, ProjectVersionsResponseSerializer,ProjectVersionsSerializer,ProjectUsersSerializer,ProjectsResponseSerializer, TestSerializer,VersionsSerializer
from django.contrib.auth.hashers import make_password, check_password
from trackerapp import util
from trackerapp.util import send, auth_cls,forgot,invite, auth, project_invite, profile_update,password_update
from django.contrib import messages
from django.conf import settings
import django_filters.rest_framework
from rest_framework import filters
import requests,ast, threading
from validate_email import validate_email
from trackerapp import templates
import datetime
from datetime import datetime, timedelta
from django.utils.timezone import datetime


@decorators.api_view(['GET'])
def usernames(request):
    data = request.data
    search = request.GET.get('search',None)
    if search != None:
        names = User.objects.filter(name__icontains=search)
        serializer = UserResponseSerializer(names, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Users"}, status=status.HTTP_200_OK )

@decorators.api_view(['GET'])
def searchprojects(request):
    data = request.data
    search = request.GET.get('search',None)
    if search != None:
        projects = Projects.objects.filter(project_name__icontains=search)
        serializer = ProjectsResponseSerializer(projects, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Projects"}, status=status.HTTP_200_OK )

@decorators.api_view(['GET'])
def searchversions(request):
    # data = request.data
    project_name=request.GET.get("project_name")
    search = request.GET.get('search',None)
    if search != None:
        projectname=Projects.objects.filter(project_name=project_name)
        projects = ProjectVersions.objects.filter(project=projectname[0],version__icontains=search)
        serializer = ProjectVersionsSerializer(projects, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Projects"}, status=status.HTTP_200_OK )

@decorators.api_view(['GET'])
@auth
def projectssearch(request):
    data = request.data
    search = request.GET.get('search',None)
    if search is not None:
        user=ProjectUsers.objects.filter(user=request.auth,project__project_name__icontains=search)       
        serializer = TestSerializer(user, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Projects"}, status=status.HTTP_200_OK )

@decorators.api_view(['GET'])
def search(request):
    data = request.data
    search = request.GET.get('search',None)
    if search != None:
        names = Projects.objects.filter(project_name__icontains=search).values_list('project_name', flat=True)
        return response.Response({'result':names,'message':"List Of Project Names"}, status=status.HTTP_200_OK )
    else:
        names = Projects.objects.values_list('project_name', flat=True)
        return response.Response({'result':names,'message':"List Of Project Names"}, status=status.HTTP_200_OK )


@decorators.api_view(['GET'])
def searchemail(request):
    data = request.data
    search = request.GET.get('search',None)
    if search != None:
        emails = User.objects.filter(email__icontains=search).values_list('email', flat=True)
        return response.Response({'result':emails,'message':"List Of Emails"}, status=status.HTTP_200_OK )
    else:
        emails = User.objects.values_list('email', flat=True)
        return response.Response({'result':emails,'message':"List Of Emails"}, status=status.HTTP_200_OK )
    


class UserAuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter() 
    serializer_class = UserSerializer
    
    @auth_cls
    def list(self, request, *args, **kwargs):
        """
            GET /userauth/
            Response Type - JSON
            List Of All Roles with/Without filter 

        """
        user = User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type=='ADMIN':
            queryset = self.get_queryset()
            serializer = UserResponseSerializer(queryset, many=True)
            return response.Response({'result':serializer.data,'message':"List Of All Users"}, status=status.HTTP_200_OK )
        else:
            return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_401_UNAUTHORIZED )

    def create(self, request, *args, **kwargs):
        """
            POST /userauth/
            Response Type - JSON
            Create/Add New User 
        """
        data = request.data
        if "name" not in data \
            or data["name"] is None \
            or not len(data["name"].strip()):
                return response.Response({"message":"Please Provide Name"},status=status.HTTP_400_BAD_REQUEST)
        if "email" not in data \
            or data["email"] is None \
            or not len(data["email"].strip()):
                return response.Response({"message":"Please Provide A Valid Email"},status=status.HTTP_400_BAD_REQUEST)

        if "designation" not in data \
            or data["designation"] is None \
            or not len(data["designation"].strip()):
                return response.Response({"message":"Please Provide Designation"},status=status.HTTP_400_BAD_REQUEST)

        if 'phone_number' in request.data:
            if len(data["phone_number"].strip()) != 10:
                return response.Response({"message":"Please Provide A Valid 10 Digit Phone Number"},status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=data['email'])
        if user.count():
            return response.Response({'message':"Email Already Exist,Please Login To Continue"},status=status.HTTP_400_BAD_REQUEST)
        token = secrets.token_urlsafe(20)
        data['name']= data['name'].capitalize()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(token=token)
        if 'HTTP_ORIGIN' in request.META:
            url = {"url":str(request.META["HTTP_ORIGIN"])+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+data['email'],"name":user[0].name}
        else:
            url = {"url":settings.IP_ADDRESS+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+data['email'],"name":user[0].name}
        email_thread= threading.Thread(target=send,args=(str(data['email']),url))
        email_thread.start()
        return response.Response({'result':serializer.data, 'message':"Verification Email Has Sent Successfully"}, status=status.HTTP_200_OK)
    

    @auth_cls
    def update(self, request, *args, **kwargs):
        """
            PUT /userauth/{id}
            Response Type - JSON
            Updates User's Details By ID
        """
        data= request.data
        user = User.objects.filter(id = request.auth.id)
        if user.count():
            queryset = self.get_object()
            if "name" not in data \
                or not len(data["name"].strip()):
                return response.Response({"message":"Please Provide Name"},status=status.HTTP_400_BAD_REQUEST)
            elif queryset.name != request.data['name']:
                queryset.name = request.data['name']
                queryset.save()
            if 'phone_number' in request.data:
                if len(data["phone_number"].strip()) == 10:
                    if queryset.phone_number != request.data['phone_number']:
                        queryset.phone_number = request.data['phone_number']
                        queryset.save()
                else:
                    return response.Response({"message":"Please Provide A Valid 10 Digit Phone Number"},status=status.HTTP_400_BAD_REQUEST)

            if "designation" not in data \
                or data["designation"] is None \
                or not len(data["designation"].strip()):
                    return response.Response({"message":"Please Provide Designation"},status=status.HTTP_400_BAD_REQUEST)
            elif queryset.designation != request.data['designation']:
                queryset.designation = request.data['designation']
                queryset.save()

            if 'HTTP_ORIGIN' in request.META:
                    hit_url=request.META["HTTP_ORIGIN"]
                    url= {"updated_at": datetime.now()+timedelta(hours=5,minutes=30),"name":user[0].name.capitalize()
                    }
            else:
                url= {"updated_at": datetime.now()+timedelta(hours=5,minutes=30),"name":user[0].name.capitalize()
                    }
            email_thread= threading.Thread(target=profile_update,args=(str(user[0].email),url))
            email_thread.start()
        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Successfully Updated"}, status=status.HTTP_200_OK )
        
    @auth_cls
    def retrieve(self, request, *args, **kwargs):
        """
            GET /userauth/{id}
            Response Type - JSON
            Retrive user_type By ID
        """
        user=User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type=='ADMIN':
            queryset = self.get_object()
            self.serializer_class = UserResponseSerializer
            serializer = self.get_serializer(queryset)
            return response.Response({'result':serializer.data,'message':"Successfully Retrived"},status=status.HTTP_200_OK )
        else:
            queryset = self.get_object()
            self.serializer_class = UserSerializer
            serializer = self.get_serializer(queryset)
            return response.Response({'result':serializer.data,'message':"Successfully Retrived"},status=status.HTTP_200_OK )
        
    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /userauth/{id}
            Response Type - JSON
            DELETE  UserBy ID

        """
        user = User.objects.filter(id=request.auth.id)
        if user.count():
            user = user[0]
            if user.user_type == 'ADMIN':
                queryset = self.get_object()
                queryset.delete()
                serializer = self.get_serializer(queryset) 
                return response.Response({'message':"Deleted Successfully"}, status=status.HTTP_200_OK )
            else:
                return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_401_UNAUTHORIZED )



@decorators.api_view(['POST'])
@auth
def admin_block(request):

    data= request.data
    # userid= request.GET.get('user_id')
    useremail= request.GET.get('user_email')
    user = User.objects.filter(id = request.auth.id)

    if user.count() and user[0].user_type =='ADMIN':
        # user_id_block= User.objects.filter(id=userid)
        user_id_block= User.objects.filter(email=useremail)

        if user_id_block.count():
            user_id_block=user_id_block[0]
            if 'is_blocked' in request.data and request.data['is_blocked']:
                user_id_block.is_blocked = request.data['is_blocked']
                user_id_block.is_active = False
                user_id_block.save()
                return response.Response({"message":"User Account Blocked Successfully"},status=status.HTTP_200_OK)
            else:
                user_id_block.is_blocked = request.data['is_blocked']
                user_id_block.is_active = True
                user_id_block.save()
                return response.Response({"message":"User Account Un-Blocked Successfully"},status=status.HTTP_200_OK)
        else:
            return response.Response({"message":"Please Provide Valid User"},status=status.HTTP_200_OK)
    else:
        return response.Response({"message":"UnAuthorised Access"},status=status.HTTP_401_UNAUTHORIZED)



@decorators.api_view(['POST'])
def user_login(request):
    """
        POST/login/
        For User Signin
        User will provide Email and Password for their account.
        On Success, User will get success message.

    """
    data = request.data
    user = User.objects.filter(email= data['email'])
    if not user.count():
        return response.Response({'message':"Email Doesnot Exist"}, status=status.HTTP_400_BAD_REQUEST)
    user = user[0] 
    if check_password(data['password'], user.password):
        if 'email' in request.data and 'password' in request.data:
            if user.is_active:
                if not user.is_blocked:
                    reset_code = secrets.token_urlsafe(20)
                    user.reset_code = reset_code
                    user.save()
                else:
                    return response.Response({'message':"Your Account Is Deactivated"}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return response.Response({'message':"Please Activate Your Account"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = UserSerializer(user)
            return response.Response({'result':serializer.data, 'message': "You Are Successfully SignedIn"}, status=status.HTTP_200_OK)
        return response.Response({'message':"Email/Password Are Required Fields"}, status=status.HTTP_401_UNAUTHORIZED)
    return response.Response({'message':"Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)


@decorators.api_view(['POST'])
def user_confirmation(request):

    """
        POST /tracker/v1.0/user_confirmation/token/email
        Response Type - JSON
        User Activation By Email&Token
    """ 
    data = request.data
    token = request.GET.get('token')
    email = request.GET.get('user')
    user = User.objects.filter(email = email, token= token)
    if not user.count():
        return response.Response({'message':"Please Provide Proper Email"}, status=status.HTTP_401_UNAUTHORIZED)
    if user[0].is_active:
        return response.Response({'message':'User Is Already Activated'}, status=status.HTTP_400_BAD_REQUEST)
    if user.count():
        user = user[0]
        user.password = make_password(data['password'])
        user.is_active = True
        user.is_blocked = False
        user.save()
        return response.Response({'message':'Successfully Created Your Account'}, status=status.HTTP_200_OK)
    return response.Response({'message':'Please Provide Proper Details'},status=status.HTTP_401_UNAUTHORIZED)

@decorators.api_view(['GET'])
@auth
def user_logout(request):
    """
        GET /user_logout/{id}
        Response Type - JSON
        Logout User By ID
    """
    access_token = request.headers['Authorization'].split('Bearer')[1].strip()
    user = User.objects.filter(reset_code=access_token)[0]
    user.reset_code = None
    user.save()
    return response.Response({'message':'Logged Out Successfully'}, status=status.HTTP_200_OK)


@decorators.api_view(['POST'])  
@auth         
def change_password(request):
    """
        POST /changepassword/
        Response Type - JSON
        Login User Can Change User Password
    """
    data = request.data
    if 'password' not in data \
        or data["password"] is None \
        or not len(data["password"].strip()):
            return response.Response({'message':"Please Provide Password"}, status=status.HTTP_400_BAD_REQUEST)
    if 'newpassword' not in data \
        or data["newpassword"] is None \
        or not len(data["newpassword"].strip()):
            return response.Response({'message':"Please Provide NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
    if 're-newpassword' not in data \
        or data["re-newpassword"] is None \
        or not len(data["re-newpassword"].strip()):
            return response.Response({'message':"Please Provide Re-NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
        
    userdetails = request.auth.reset_code
    user = User.objects.filter(reset_code= userdetails)
    if user.count():
        user = user[0]
        useremail= user.email
        name= user.name.capitalize()
    else:
        return response.Response({'message':"User Not Found"}, status=status.HTTP_400_BAD_REQUEST)
    if check_password(data['password'], user.password):
        if user.is_active:            
            if request.data['newpassword'] != request.data['re-newpassword']:
                return response.Response({'message':"NewPassword Not Matched With Re-NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
            else:                
                if 'HTTP_ORIGIN' in request.META:
                    hit_url=request.META["HTTP_ORIGIN"]
                    url= {"updated_at":datetime.now()+timedelta(hours=5,minutes=30),"name":name
                    }
                else:
                    url= {"updated_at":datetime.now()+timedelta(hours=5,minutes=30),"name":name
                    }
                email_thread= threading.Thread(target=password_update,args=(str(useremail),url))
                email_thread.start()
                user.password = make_password(data['newpassword'])  
                user.save()
                serializer= UserSerializer(user)
                return response.Response({ 'result':serializer.data,'message': "Your Password Has Changed Successfully"}, status=status.HTTP_200_OK)
        else:
            return response.Response({'message':"Your Account Is InActive"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return response.Response({'message':"Please Provide Previous Password"}, status=status.HTTP_400_BAD_REQUEST)


@decorators.api_view(['POST'])
def password(request):
    data = request.data    
    email = data['email']   
    user = User.objects.filter(email = email)
    name= user[0].name.capitalize()
    if not user.count():
        return response.Response({'message':'Email Doesnot Exist'}, status=status.HTTP_400_BAD_REQUEST)
    token = secrets.token_urlsafe(20)
    if user.count():
        user=user[0]
        user.token=token
        user.save()
    if 'HTTP_ORIGIN' in request.META:
        url={      
        "url": str(request.META["HTTP_ORIGIN"])+'/forgot/password/?token='+str(token)+'&user='+data['email'],
        "name":name}
    else:
        url={ 
        "url": settings.IP_ADDRESS+'/forgot/password/?token='+str(token)+'&user='+data['email'],"name":name}
    email_thread= threading.Thread(target=forgot,args=(str(data['email']),url))
    email_thread.start()
    return response.Response({'message':"Forgot Password Link Has Sent To Your your Email"}, status=status.HTTP_200_OK)


@decorators.api_view(['POST'])
def forgot_password(request):
    data= request.data
    token = request.GET.get('token')
    email = request.GET.get('user')

    user = User.objects.filter(email = email, token= token)
    if not user.count():
        return response.Response({'message':'Email Doesnot Exist'}, status=status.HTTP_400_BAD_REQUEST)
    if user.count():
        user = user[0]
        user.password = make_password(data['newpassword'])
        user.save()
        return response.Response({'message':'Password Changed Succcessfully'}, status=status.HTTP_200_OK)
    return response.Response({'message':'Please provide Proper Details'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectsViewSet(viewsets.GenericViewSet):
    queryset = Projects.objects.all() 
    serializer_class = ProjectsSerializer
    
    @auth_cls
    def list(self, request, *args, **kwargs):
        """
            GET /ProjectDetails/
            Response Type - JSON
            List Of All ProjectDetails
        """       
        user=User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type =='ADMIN':
            queryset = Projects.objects.all()
            serializer = ProjectsSerializer(queryset, many=True)
            return response.Response({'result':serializer.data,'message':"List Of All Users Project Details"}, status=status.HTTP_200_OK )           
  
        if user.count():
            queryset= Projects.objects.filter(id__in=ProjectUsers.objects.filter(user=request.auth.id).values_list('project_id', flat=True))
            serializer = ProjectsSerializer(queryset, many=True)
            return response.Response({'result':serializer.data,'message':"List Of  User Projects"}, status=status.HTTP_200_OK )

    @auth_cls
    def retrieve(self, request, *args, **kwargs):
        """
            GET /ProjectDetails/{id}
            Response Type - JSON
            List Of Particular ProjectDetails By ID
        """
        data=request.data
        user=User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type=='ADMIN':
            queryset = self.get_object()
            serializer = ProjectsResponseSerializer(queryset)
            return response.Response({'result':serializer.data,'message':"List Of  Project Details"}, status=status.HTTP_200_OK )
        else:
            queryset = self.get_object()
            serializer = ProjectsResponseSerializer(queryset)
            return response.Response({'result':serializer.data,'message':"List Of Project Details"}, status=status.HTTP_200_OK)

    @auth_cls
    def create(self, request, *args, **kwargs):
        """
            POST /ProjectDetails/
            Response Type - JSON
            Create's User ProjectDetails
        """
        data=request.data
        user=User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type=='ADMIN':
            for each in data['developers']:
                if not validate_email(each['email']):
                    return response.Response({"message":"Please Provide Valid Email"+str(each['email'])})


        if "project_name" not in data \
            or data["project_name"] is None \
            or not len(data["project_name"].strip()):
                return response.Response({"message":"Please Provide A Valid Project Name"},status=status.HTTP_400_BAD_REQUEST)
        if "version" not in data \
            or data["version"] is None \
            or not len(data["version"].strip()):
                return response.Response({"message":"Please Provide A Valid version"},status=status.HTTP_400_BAD_REQUEST)
        if "repo_url" in data:
            if validators.url(data['repo_url']):
                pass
            else:
                return response.Response({"message":"Please Provide A Valid Repository URL"},status=status.HTTP_400_BAD_REQUEST)
        if "postman_link" in data and data['postman_link'] and len(data['postman_link'].strip()):
            if validators.url(data['postman_link']):
                pass 
            else:
                return response.Response({"message":"Please Provide A Valid Postman Link"},status=status.HTTP_400_BAD_REQUEST)
        project = Projects.objects.filter(project_name=data['project_name'])
        if project.count():            
            project= project[0]
            pro_ver = ProjectVersions.objects.filter(project=project)
            if pro_ver.count() and pro_ver[0].version.lower()==data['version'].lower():
                return response.Response({'message':'Project Details Already Exist'},status=status.HTTP_400_BAD_REQUEST)
            if "is_hosted" in request.data and request.data["is_hosted"]:
                if "hosted_username" not in data \
                    or data["hosted_username"] is None \
                    or not len(data["hosted_username"].strip()):
                        return response.Response({"message":"Please Provide A Valid Hosted Username "},status=status.HTTP_400_BAD_REQUEST)
                if "hosted_password" not in data \
                    or data["hosted_password"] is None \
                    or not len(data["hosted_password"].strip()):
                        return response.Response({"message":"Please Provide A Valid Hosted Password"},status=status.HTTP_400_BAD_REQUEST)
                if "hosted_ip_address" not in data \
                    or data["hosted_ip_address"] is None \
                    or not len(data["hosted_ip_address"].strip()):
                        return response.Response({"message":"Please Provide A Valid Hosted-IP Address"},status=status.HTTP_400_BAD_REQUEST)

                if "application_url" not in data \
                    or data["application_url"] is None \
                    or not len(data["application_url"].strip()):
                        return response.Response({"message":"Please Provide A Application URL "},status=status.HTTP_400_BAD_REQUEST)
                elif validators.url(data['application_url']):
                        pass
                else:
                    return response.Response({"message":"Please Provide A Valid Application URL"},status=status.HTTP_400_BAD_REQUEST)
       
                if "application_username" not in data \
                    or data["application_username"] is None \
                    or not len(data["application_username"].strip()):
                        return response.Response({"message":"Please Provide A Valid Application Username"},status=status.HTTP_400_BAD_REQUEST)
                if "application_password" not in data \
                    or data["application_password"] is None \
                    or not len(data["application_password"].strip()):
                        return response.Response({"message":"Please Provide A Valid Application Password"},status=status.HTTP_400_BAD_REQUEST)

                if "application_user_type" not in data \
                    or data["application_user_type"] is None \
                    or not len(data["application_user_type"].strip()):
                        return response.Response({"message":"Please Provide A Valid Application UserType"},status=status.HTTP_400_BAD_REQUEST)

                project_version=ProjectVersions.objects.create(
                    project=project,
                    created_by=request.auth,
                    updated_by=request.auth,
                    repo_url = data['repo_url'],
                    repo_username = data['repo_username'],
                    repo_password = data['repo_password'],
                    repo_branch= data['repo_branch'],
                    is_hosted=data['is_hosted'],
                    hosted_username=data['hosted_username'],
                    hosted_password=data['hosted_password'],
                    hosted_ip_address=data['hosted_ip_address'],
                    application_url=data['application_url'],
                    application_username=data['application_username'],
                    application_password=data['application_password'],
                    application_user_type=data['application_user_type'],
                    version=data['version'].capitalize(),
                    postman_link=data['postman_link'] if data['postman_link'] and len(data['postman_link'].strip()) else None,
                    status=data['status']
                )

            else:
                project_version=ProjectVersions.objects.create(
                    project=project,
                    created_by=request.auth,
                    updated_by=request.auth,
                    repo_url = data['repo_url'],
                    repo_username = data['repo_username'],
                    repo_password = data['repo_password'],
                    repo_branch= data['repo_branch'],
                    postman_link=data['postman_link'] if data['postman_link'] and len(data['postman_link'].strip()) else None,
                    status=data['status'],
                    is_hosted=data['is_hosted'],
                    version=data['version'].capitalize()
                )

            user=User.objects.filter(id=request.auth.id)
            if user.count() and user[0].user_type=='ADMIN':
                if "developers" not in data \
                    or data["developers"] is None:
                        return response.Response({"message":"Please Provide Valid Developers"},status=status.HTTP_400_BAD_REQUEST)
                if 'developers' in request.data:
                    for each in data['developers']:
                        user=User.objects.filter(email=each['email'])
                        if not user.count():
                            token = secrets.token_urlsafe(20)
                            user=User.objects.create(email=each['email'],name=each['email'].split('@')[0], token= token)
                            user_name= user.name.capitalize()
                            if 'HTTP_ORIGIN' in request.META:
                                url= {"url":str(request.META["HTTP_ORIGIN"])+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+each['email'],"name":user_name}

                            else:
                                url= {"url":settings.IP_ADDRESS+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+each['email'],"name":user_name}

                            email_thread= threading.Thread(target=invite,args=(str(each['email']),url))
                            email_thread.start()
                             
                            project_user=ProjectUsers.objects.create(project=project,user=user,role=each['role'],version= project_version)
                        else:
                            project_user=ProjectUsers.objects.create(project=project,user=user[0],role=each['role'],version= project_version)
            else: 
                project_user=ProjectUsers.objects.create(project=project,user=user[0],role=data['role'], version= project_version)
             

        else:
            project=Projects.objects.create(
                project_name=data['project_name'],
                created_by=request.auth,
                updated_by=request.auth,            
                )
            if "is_hosted" in request.data and request.data["is_hosted"]:                
                project_version=ProjectVersions.objects.create(
                    project=project,
                    created_by=request.auth,
                    updated_by=request.auth,
                    repo_url = data['repo_url'],
                    repo_username = data['repo_username'],
                    repo_password = data['repo_password'],
                    repo_branch= data['repo_branch'],
                    is_hosted=data['is_hosted'],
                    hosted_username=data['hosted_username'],
                    hosted_password=data['hosted_password'],
                    hosted_ip_address=data['hosted_ip_address'],
                    application_url=data['application_url'],
                    application_username=data['application_username'],
                    application_password=data['application_password'],
                    application_user_type=data['application_user_type'],
                    version=data['version'].capitalize(),
                    postman_link=data['postman_link'] if data['postman_link'] and len(data['postman_link'].strip()) else None,
                    status=data['status']
                )
            else:
                project_version=ProjectVersions.objects.create(
                    project=project,
                    created_by=request.auth,
                    updated_by=request.auth,
                    repo_url = data['repo_url'],
                    repo_username = data['repo_username'],
                    repo_password = data['repo_password'],
                    repo_branch= data['repo_branch'],
                    postman_link=data['postman_link'] if data['postman_link'] and len(data['postman_link'].strip()) else None,
                    status=data['status'],
                    is_hosted=data['is_hosted'],
                    version=data['version'].capitalize()
                )
            user=User.objects.filter(id=request.auth.id)
            if user.count() and user[0].user_type=='ADMIN':
                if "developers" not in data \
                    or data["developers"] is None:
                        return response.Response({"message":"Please Provide Valid Developers"},status=status.HTTP_400_BAD_REQUEST)
                if 'developers' in request.data:
                    for each in data['developers']:
                        user=User.objects.filter(email=each['email'])
                        if not user.count():
                            token = secrets.token_urlsafe(20)
                            user=User.objects.create(email=each['email'],name=each['email'].split('@')[0], token= token)
                            user_name= user.name.capitalize()
                            if 'HTTP_ORIGIN' in request.META:
                                url= {"url":str(request.META["HTTP_ORIGIN"])+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+each['email'],"name":user_name}

                            else:
                                url= {"url":settings.IP_ADDRESS+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+each['email'],"name":user_name}

                            email_thread= threading.Thread(target=invite,args=(str(each['email']),url))
                            email_thread.start()
                            project_user=ProjectUsers.objects.create(project=project,user=user,role=each['role'],version= project_version)
                        else:
                            project_user=ProjectUsers.objects.create(project=project,user=user[0],role=each['role'],version= project_version)
            else: 
                project_user=ProjectUsers.objects.create(project=project,user=user[0],role=data['role'], version= project_version)
        
        serializer=ProjectsSerializer(project)
        response_data= serializer.data
        response_data['versions']= ProjectVersionsSerializer(project_version).data
        return response.Response({'result':response_data, 'message':"Created Successfully"}, status=status.HTTP_200_OK)
            
    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /projectdetails/{id}
            Response Type - JSON
            Deleting A Projects
        """
        user= User.objects.filter(id=request.auth.id)
        if user.count() and ((user[0].user_type=='ADMIN') or (user[0].designation=="TEAM_LEAD")):
            queryset = self.get_object()
            queryset.delete()
            serializer = self.get_serializer(queryset) 
            return response.Response({'result':serializer.data,'message':"Deleted Successfully"}, status=status.HTTP_200_OK )
        else:
            return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_400_BAD_REQUEST )
    
class ProjectVersionsViewSet(viewsets.GenericViewSet):
    
    queryset = ProjectVersions.objects.filter() 
    serializer_class = ProjectVersionsSerializer

    @auth_cls
    def list(self, request, *args, **kwargs):

        user=User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type =='ADMIN':
            queryset = ProjectVersions.objects.all()
            serializer = ProjectVersionsSerializer(queryset, many=True)
            return response.Response({'result':serializer.data,'message':"List Of All Project Versions Details"}, status=status.HTTP_200_OK )           
        if user.count():
            queryset= ProjectUsers.objects.filter(user=request.auth.id)
            serializer = TestSerializer(queryset, many=True)
            return response.Response({'result':serializer.data,'message':"List Of Project Versions"}, status=status.HTTP_200_OK )
 

    @auth_cls
    def update(self, request, *args, **kwargs):
        """
            PUT /ProjectVersions/{id}
            Response Type - JSON
            Update User ProjectVersios By ID
        """
        queryset = self.get_object()
        data=request.data
        need_to_save = False    

        if 'repo_url' in request.data:
            if validators.url(data['repo_url']):
                if queryset.repo_url != request.data['repo_url']:
                    queryset.repo_url= request.data['repo_url']
                    need_to_save=True
            else:
                return response.Response({"message":"Please Provide A Valid Repository URL"},status=status.HTTP_400_BAD_REQUEST)

        if 'status' in request.data:
            if queryset.status != request.data['status']:
                queryset.status = request.data['status']
                need_to_save=True
        if 'postman_link' in data and data['postman_link'] and len(data['postman_link'].strip()):
            if validators.url(data['postman_link']):
                if queryset.postman_link != request.data['postman_link']:
                    queryset.postman_link = request.data['postman_link']
                    need_to_save=True
            else:
                return response.Response({"message":"Please Provide A Valid Postman Link"},status=status.HTTP_400_BAD_REQUEST)
        if 'repo_username' in request.data:
            if queryset.repo_username != request.data['repo_username']:
                queryset.repo_username = request.data['repo_username']
                need_to_save=True
        if 'repo_password' in request.data:
            if queryset.repo_password != request.data['repo_password']:
                queryset.repo_password = request.data['repo_password']
                need_to_save=True
        if 'repo_branch' in request.data:
            if queryset.repo_branch != request.data['repo_branch']:
                queryset.repo_branch = request.data['repo_branch']
                need_to_save=True    
        if 'is_hosted' in request.data:
            if queryset.is_hosted != request.data['is_hosted']:
                queryset.is_hosted = request.data['is_hosted']
                need_to_save=True
        if 'hosted_username' in request.data:
            if queryset.hosted_username != request.data['hosted_username']:
                queryset.hosted_username = request.data['hosted_username']
                need_to_save=True
        if 'hosted_password' in request.data:
            if queryset.hosted_password != request.data['hosted_password']:
                queryset.hosted_password = request.data['hosted_password']
                need_to_save=True
        if 'hosted_ip_address' in request.data:
            if queryset.hosted_ip_address != request.data['hosted_ip_address']:
                queryset.hosted_ip_address = request.data['hosted_ip_address']    
                need_to_save=True
        if 'application_url' in request.data:
            if validators.url(data['application_url']):
                if queryset.application_url != request.data['application_url']:
                    queryset.application_url= request.data['application_url']
                    need_to_save=True
            else:
                return response.Response({"message":"Please Provide A Valid Application URL"},status=status.HTTP_400_BAD_REQUEST)
                
        if 'application_username' in request.data:
            if queryset.application_username != request.data['application_username']:
                queryset.application_username = request.data['application_username']
                need_to_save=True
        if 'application_password' in request.data:
            if queryset.application_password != request.data['application_password']:
                queryset.application_password = request.data['application_password']    
                need_to_save=True
        if 'application_user_type' in request.data:
            if queryset.application_user_type != request.data['application_user_type']:
                queryset.application_user_type = request.data['application_user_type']    
                need_to_save=True
        if need_to_save:    
            queryset.updated_by=request.auth
            queryset.save()

        serializer = ProjectVersionsSerializer(queryset)
        return response.Response({'result':serializer.data,'message':"Successfully Updated"}, status=status.HTTP_200_OK )
    @auth_cls
    def delete(self, request, *args, **kwargs):
        user= User.objects.filter(id=request.auth.id)
        if user.count() and user[0].user_type=='ADMIN':
            queryset = self.get_object()
            queryset.delete()
            serializer = self.get_serializer(queryset) 
            return response.Response({'message':"Deleted Successfully"}, status=status.HTTP_200_OK )
        else:
            return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_400_BAD_REQUEST )


@decorators.api_view(['GET'])
@auth                                                          
def project_versions(request):
    data=request.data
    project=request.GET.get('project_id')
    user= User.objects.filter(id= request.auth.id)
    if user.count() and user[0].user_type =='ADMIN':
        user_=ProjectVersions.objects.filter(project=project)
        serializer=ProjectVersionsSerializer(user_,many=True)
        return response.Response({'result':serializer.data,"message":"List Of Project versions"},status=status.HTTP_200_OK)
    else:
        user1=ProjectUsers.objects.filter(project=project,user= request.auth)
        serializer=ProjectUsersSerializer(user1,many=True)
        return response.Response({'result':serializer.data,"message":"List Of Project versions"},status=status.HTTP_200_OK)

@decorators.api_view(['GET'])
@auth                                                          
def project_details(request):
    data = request.data
    version = request.GET.get('version_id')
    user= User.objects.filter(id=request.auth.id)
    pr_ver= ProjectVersions.objects.filter(id=version,created_by=user[0])
    if (user.count() and (user[0].user_type =='ADMIN')) or (pr_ver.count() and (pr_ver[0].created_by== request.auth)):
        details = ProjectVersions.objects.filter(id=version)
        if not details.count():
            return response.Response({"message": "Please Provide Valid Version"}, status=status.HTTP_400_BAD_REQUEST)
        details=details[0]
        serializer=ProjectVersionsSerializer(details)
        return response.Response({'result':serializer.data,"message":"Version Details"},status=status.HTTP_200_OK)
    else:
        details = ProjectVersions.objects.filter(id=version)
        details=details[0]
        serializer=UserVersionsSerializer(details)
        return response.Response({'result':serializer.data,"message":"Version Details"},status=status.HTTP_200_OK)
    

@decorators.api_view(['GET'])
@auth                                                          
def user_projects(request):
    data=request.data
    user=request.GET.get('user_id')
    user_projects=ProjectUsers.objects.filter(user=user).values_list('project_id', flat=True)
    projects= Projects.objects.filter(id__in=user_projects)
    serializer=ProjectsSerializer(projects,many=True)
    return response.Response({'result':serializer.data,"message":"List Of Projects"},status=status.HTTP_200_OK)

@decorators.api_view(['POST'])
@auth                                                          
def user_add(request):

    data=request.data
    version_id= request.GET.get('ver_id')

    if "project_name" not in data \
        or data["project_name"] is None \
        or not len(data["project_name"].strip()):
            return response.Response({"message":"Please Provide A Valid Project Name"},status=status.HTTP_400_BAD_REQUEST)
    if "developers" not in data \
        or data["developers"] is None \
        or not len(data["developers"].strip()):
            return response.Response({"message":"Please Provide Valid Developers"},status=status.HTTP_400_BAD_REQUEST)
    if "role" not in data \
        or data["role"] is None \
        or not len(data["role"].strip()):
            return response.Response({"message":"Please Provide A Valid Role"},status=status.HTTP_400_BAD_REQUEST)
    project_name=data['project_name']
    projectname=Projects.objects.filter(project_name=data["project_name"])
    if not projectname.count():
        return response.Response({"message":"Please Provide A Valid Project"}, status=status.HTTP_400_BAD_REQUEST)
    project_role=data['role']
    project_ver= ProjectVersions.objects.filter(id = version_id,project=projectname[0])
    if not project_ver.count():
        return response.Response({"message":"Please Provide A Valid Version"}, status=status.HTTP_400_BAD_REQUEST)
    user=User.objects.filter(id=request.auth.id)
    if user.count():       
        usermail = data['developers']
        project=Projects.objects.filter(project_name=project_name)
        if project.count():
            prouser=User.objects.filter(email=usermail)
            if not prouser.count():
                token = secrets.token_urlsafe(20)
                createuser=User.objects.create(email=usermail,name=usermail.split('@')[0],token=token)
                create_name=createuser.name.capitalize()
                if 'HTTP_ORIGIN' in request.META:
                    url={"url": str(request.META["HTTP_ORIGIN"])+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+str(usermail),"name":create_name}
                else:
                    url= {"url":settings.IP_ADDRESS+'/tracker/v1.0/user_confirmation/?token='+str(token)+'&user='+str(usermail),"name":create_name}
                email_thread= threading.Thread(target=invite,args=(str(usermail),url))
                email_thread.start()
                pro_users=ProjectUsers.objects.create(project=project[0],user=createuser,role=project_role,version= project_ver[0])
                serializer=ProjectUsersSerializer(pro_users)
                return response.Response({'result':serializer.data,"message":"Successfully Added To The Version"},status=status.HTTP_200_OK)                
            else:
                prouser_name= prouser[0].name.capitalize()
                pro_users=ProjectUsers.objects.filter(project=project[0],version= project_ver[0], user= prouser[0])
                if pro_users.count():
                    return response.Response({"message":"You Are Already Exist In Version "},status=status.HTTP_400_BAD_REQUEST)
                else:
                    if 'HTTP_ORIGIN' in request.META:
                        url= {"url":str(request.META["HTTP_ORIGIN"])+'/login/',"name":prouser_name}
                    else:
                        url= {"url":settings.IP_ADDRESS+'/login/',"name":prouser_name}
                    email_thread= threading.Thread(target=project_invite,args=(str(usermail),url))
                    email_thread.start()
                    project_user=ProjectUsers.objects.create(role=project_role,user=prouser[0],project=project[0], version= project_ver[0])
                    serializer=ProjectUsersSerializer(project_user)
                    return response.Response({'result':serializer.data,"message":"Successfully Added To The Version"},status=status.HTTP_200_OK)
        else:
            return response.Response({"message":"Please Provide Valid Project Name"},status=status.HTTP_400_BAD_REQUEST)

@decorators.api_view(['DELETE'])
@auth
def user_delete(request):
    data=request.data
    user_id=request.GET.get("user_id")
    user=User.objects.filter(id=request.auth.id)
    if user.count() and ((user[0].user_type=='ADMIN') or (user[0].designation=="TEAM_LEAD")):   
        project_user=ProjectUsers.objects.filter(id=user_id)
        if project_user.count():
            project_user[0].delete()
            serializer=ProjectUsersSerializer(project_user)
            return response.Response({"message":"Successfully Deleted From The Version"},status=status.HTTP_200_OK)
        else:
            return response.Response({'message':"You Are Not A Part Of This Version"}, status=status.HTTP_400_BAD_REQUEST )
    else:
        return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_400_BAD_REQUEST )

class ProjectUsersViewSet(viewsets.GenericViewSet):
    
    queryset = ProjectUsers.objects.filter() 
    serializer_class = ProjectUsersSerializer
    @auth_cls
    def update(self, request, *args, **kwargs):
        """
            PUT /ProjectVersions/{id}
            Response Type - JSON
            Update User ProjectVersios By ID
        """
        queryset = self.get_object()
        data=request.data
        user=User.objects.filter(id=request.auth.id)
        if user.count() and ((user[0].user_type=="ADMIN") or (user[0].designation=='TEAM_LEAD') or (user[0].designation=='PROJECT_MANAGER')):
            need_to_save = False                      

            if 'role' in request.data:
                queryset.role = request.data['role']
                need_to_save=True
            if need_to_save:
                queryset.save()
            serializer = ProjectUsersSerializer(queryset)
            return response.Response({'result':serializer.data,'message':"Successfully Updated"}, status=status.HTTP_200_OK )
        else:
            return response.Response({'message':"UnAuthorised Access"}, status=status.HTTP_400_BAD_REQUEST )

@decorators.api_view(['POST'])
@auth                                                          
def normal_user_add(request):
    """
    POST /normaluser/
    Response Type - JSON
    Normal User Can Add In Existing Project, If Project Already Exists
    """
    data=request.data
    if "project_name" not in data \
        or data["project_name"] is None \
        or not len(data["project_name"].strip()):
            return response.Response({"message":"Please Provide A Valid Project Name"},status=status.HTTP_400_BAD_REQUEST)
    if "role" not in data \
        or data["role"] is None \
        or not len(data["role"].strip()):
            return response.Response({"message":"Please Provide A Valid Role"},status=status.HTTP_400_BAD_REQUEST)
    project_name=data['project_name']
    project_role=data['role']
    version_id= request.GET.get('ver_id')
    project=Projects.objects.filter(project_name=project_name)
    if not project.count():
        return response.Response({"message":"Please Provide A Valid Project"},status=status.HTTP_400_BAD_REQUEST)

    project_vers= ProjectVersions.objects.filter(id= version_id, project= project[0])
    if not project_vers.count():
        return response.Response({"message":"Please Provide A Valid Version"},status=status.HTTP_400_BAD_REQUEST)

    if project_vers.count():
        pro_users=ProjectUsers.objects.filter(project=project[0], user=request.auth, version= project_vers[0])
        if pro_users.count():
            return response.Response({"message":"You Are Already Exists In This Version "},status=status.HTTP_400_BAD_REQUEST)        
        project_user=ProjectUsers.objects.create(role=project_role,user=request.auth,project=project[0], version= project_vers[0])
        serializer=ProjectUsersSerializer(project_user)
        return response.Response({'result':serializer.data,"message":"You Are Successfully Added To The Version"},status=status.HTTP_200_OK)
    else:
        return response.Response({'message':"Please Provide Valid Project Name"}, status=status.HTTP_400_BAD_REQUEST )


@decorators.api_view(['GET'])
def job_choices(request):
    """
    GET List of JOB CHOICES
    """
    data= models.JOB_CHOICES
    return response.Response({'result':data})

@decorators.api_view(['GET'])
def user_blocking(request):

    data=request.data
    userid= request.GET.get('user_id')
    userblock= request.GET.get('user_block')

    user= User.objects.filter(id=userid)
    if not user.count():
        return response.Response({"message":"Please Provide Valid User"}, status=status.HTTP_400_BAD_REQUEST)
    
     