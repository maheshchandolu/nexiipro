from django.shortcuts import render

# Create your views here.

import secrets, os, magic, random, datetime
from django.utils.timezone import utc
from django.utils import timezone
from datetime import datetime, timedelta
from . import models
from nexiiapp.models import User, Requirement, Upload, UserSecret, UserToken, UserCredit, UserType, TransactionHistory, AccountDetails
from rest_framework import viewsets, response, decorators, status
from rest_framework.decorators import action
from . serializers import UserSerializer, RequirementSerializer, UploadSerializer, UserTypeSerializer, UserSecretSerializer
from . serializers import UserCreditSerializer, TransactionHistorySerializer, AccountDetailsSerializer, UserTokenSerializer
from django.contrib.auth.hashers import make_password, check_password
from nexiiapp import util
from nexiiapp.util import send, auth, auth_cls, forgot
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.contrib import messages
from decimal import *





class UserAuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter() 
    serializer_class = UserSerializer
    # permission_class = (IsAuthenticated)
    
    @auth_cls
    def list(self, request, *args, **kwargs):
        """
            GET /userauth/
            Response Type - JSON
            List Of All Roles with/Without filter 

        """
        user= request.auth.user.id
        user_secret= UserSecret.objects.filter(user= user,is_admin= True)
        if user_secret.count():
            user_secret= user_secret[0]
        else:
            return response.Response({'message':"You Have NO Access Here"}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['actor'] = request.auth.user.id
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return response.Response({'result':serializer.data,'message':"List Of All Users"}, status=status.HTTP_200_OK )

    # @auth_cls
    def create(self, request, *args, **kwargs):
        """
            POST /userauth/
            Response Type - JSON
            Create/Add New User 
        """
        data= request.data
        token = secrets.token_urlsafe(20)
        # data['token']= token
        user= User.objects.create(user_name = data['user_name'],email = data['email'])
        user_token= UserToken.objects.create(token = token,user = user)
        user_secret= UserSecret.objects.create(user = user)
        user_credit= UserCredit.objects.create(actor= user)        
        user_queryset=UserSerializer(user)
        user_secret= UserSecret.objects.filter(user = user)
        if 'is_admin' in request.data:
            if user_secret.count():
                user_secret= user_secret[0]
                user_secret.is_admin= request.data['is_admin']
                user_secret.save()
        url= 'http://127.0.0.1:8001/cvbank/v1/user_confirmation/?token='+str(token)+'&user='+data['email']
        send(data['email'],url)
        return response.Response({'result':user_queryset.data, 'message':"Verification Email Has Sent Successfully"}, status=status.HTTP_200_OK)

    @auth_cls
    def update(self, request, *args, **kwargs):

        """
            PUT /userauth/{id}
            Response Type - JSON
            Updates User's Details By ID
        """
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()

        if 'user_name' in request.data:
            queryset.user_name = request.data['user_name']
            queryset.save()

        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Successfully Updated"}, status=status.HTTP_200_OK )

    @auth_cls
    def retrieve(self, request, *args, **kwargs):
        """
            GET /userauth/{id}
            Response Type - JSON
            Retrive Role By ID

        """
        user= request.auth.user.id
        user_secret= UserSecret.objects.filter(user= user,is_admin= True)
        if user_secret.count():
            user_secret= user_secret[0]
        else:
            return response.Response({'message':"You Have NO Access Here"}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()
        self.serializer_class = UserSecretSerializer

        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"User Successfully Retrived"},status=status.HTTP_200_OK )

    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /userauth/{id}
            Response Type - JSON
            DELETE  UserBy ID

        """
        user= request.auth.user.id
        user_secret= UserSecret.objects.filter(user= user,is_admin= True)
        if user_secret.count():
            user_secret= user_secret[0]
        else:
            return response.Response({'message':"You Have NO Access Here"}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['actor'] = request.auth.user.id
        self.queryset = UserSecret.objects.filter()
        queryset = self.get_object()
        queryset.delete()
        serializer = self.get_serializer(queryset)
        return response.Response({'result': serializer.data, 'message': "User Is Successfully Deleted"}, status=status.HTTP_200_OK )

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
        return response.Response("email doesnot exist")

    user_secret=UserSecret.objects.filter(user=user[0])
    if not len(user_secret):
        return response.Response({'message':"User Doesn't Exist"}, status=status.HTTP_400_BAD_REQUEST)
    user_secret=user_secret[0]
    if check_password(data['password'], user_secret.password):
        if 'email' in request.data and 'password' in request.data:
            if user_secret.is_active:
                if not user_secret.is_blocked:
                    reset_code = secrets.token_urlsafe(20)
                    display_name= user[0].email.split('@')[0]
                    user_secret.reset_code= reset_code
                    user_secret.display_name= display_name
                    user_secret.save()
                    user_token = UserToken.objects.filter(user=user[0])
                    if user_token.count():
                        user_token= user_token[0]
                        user_token.expired_at=  datetime.now(timezone.utc)+timedelta(hours=48)
                        user_token.save()
                else:
                    return request.Response({'message':"Your Account is Deactivated"}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return request.Response({'message':"Please Activate Your Account"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer= UserSecretSerializer(user_secret)
            return response.Response({'result':serializer.data, 'message': "You Are Successfully SignedIn"}, status=status.HTTP_200_OK)
        return response.Response({'message':"Email/Password are required Fields"}, status=status.HTTP_401_UNAUTHORIZED)
    return response.Response({'message':"Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)





@decorators.api_view(['POST'])
def user_confirmation(request):

    """
        POST /cvbank/v1/user_confirmation/token/email
        Response Type - JSON
        User Activation By Email&Token
    """ 
    data= request.data
    token = request.GET.get('token')
    email = request.GET.get('user')

    user = User.objects.filter(email = email)
    if not user.count():
        return response.Response({'result':"Please provide proper email"}, status=status.HTTP_400_BAD_REQUEST)
    user_token = UserToken.objects.filter(user = user[0])
    # user_token = user_token[]
    if user_token.count():
        user_secret = UserSecret.objects.filter(user = user[0])
        # user_secret = user_secret[0]
    if user_secret[0].is_active:
        return response.Response({'result':"User is Already Activated"}, status=status.HTTP_201_CREATED)
    if user_secret.count():
        user_secret = user_secret[0]
        user_secret.password = make_password(data['password'])
        user_secret.is_active = True
        user_secret.is_blocked = False
        user_secret.save()
        return response.Response({'message':"Successfully Created"}, status=status.HTTP_200_OK)
    return response.Response({'result':"Please provide Proper Details"}, status=status.HTTP_400_BAD_REQUEST)


@decorators.api_view(['GET'])
@auth
def user_logout(request):
    """
        GET /user_logout/{id}
        Response Type - JSON
        Logout User By ID
    """
    access_token= request.headers['Authorization'].split('Bearer')[1].strip()
    user=UserSecret.objects.filter(reset_code=access_token)[0]
    user.reset_code=None
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

    data= request.data
    if 'password' not in data:
        return response.Response({'message':"Please Provide OLD Password"}, status=status.HTTP_400_BAD_REQUEST)
    if 'newpassword' not in data:
        return response.Response({'message':"Please Provide NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
    if 're-newpassword' not in data:
        return response.Response({'message':"Please Provide Re-NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
    userdetails= request.auth.reset_code
    user= UserSecret.objects.filter(reset_code= userdetails)
    if user.count():
        user= user[0]
    else:
        return response.Response({'message':"User Not Found"}, status=status.HTTP_400_BAD_REQUEST)
    if check_password(data['password'], user.password):
        if 'password' in request.data:
            if user.is_active:            
                if request.data['newpassword'] != request.data['re-newpassword']:
                    return response.Response({'message':"New & Re-new Password Doesnot Match"}, status=status.HTTP_400_BAD_REQUEST)
                else:                
                    user.password = make_password(data['newpassword'])  
                    user.save()
                    serializer= UserSecretSerializer(user)
            return response.Response({ 'result':serializer.data,'message': "Your Password Changed Successfully"}, status=status.HTTP_200_OK)
        else:
            return response.Response({'message':"Your Account is InActive"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return response.Response({'message':"Please Provide OLD Password"}, status=status.HTTP_400_BAD_REQUEST)



class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.filter() 
    serializer_class = RequirementSerializer
    
    @auth_cls
    def list(self, request, *args, **kwargs):
        """
            GET /requirement/
            Response Type - JSON
            List Of All Requirements 
        """

        request.data['actor'] = request.auth.user.id
        queryset = self.get_queryset()
        queryset= queryset.filter(actor=request.auth.user)
        serializer = RequirementSerializer(queryset, many=True)
        return response.Response({'result':serializer.data,'message':"List Of All User Requirements"}, status=status.HTTP_200_OK )

    @auth_cls
    def create(self, request, *args, **kwargs):
        """
            POST /requirement/
            Response Type - JSON
            Create's User Requirements
        """
        request.data['actor'] = request.auth.user.id
        credit= [2,3,4,5,6,7,8,9]
        request.data['score']= random.choice(credit)
        user_queryset = self.get_serializer(data=request.data)
        user_queryset.is_valid(raise_exception=True)
        user_queryset.save()
        user_requirement= Requirement.objects.filter(actor= request.auth.user)
        if user_requirement.count():
            user_requirement= user_requirement[0]
            transaction_history= TransactionHistory.objects.create(actor=request.auth.user,requirement_id= user_requirement)
            account_details= AccountDetails.objects.create(actor=request.auth.user,requirement_id= user_requirement)



        return response.Response({'result':user_queryset.data, 'message':"Requirements Sent Successfully"}, status=status.HTTP_200_OK)

    @auth_cls
    def update(self, request, *args, **kwargs):
        """
            PUT /requirement/{id}
            Response Type - JSON
            Update User Requirements By ID
        """
        
        queryset = self.get_object()
        need_to_save = False

        if 'technical_skills' in request.data:
            queryset.technical_skills = request.data['technical_skills']
            need_to_save = True
        if 'job_role' in request.data:
            queryset.job_role = request.data['job_role']
            need_to_save = True
        if 'min_experience' in request.data:
            queryset.min_experience = request.data['min_experience']
            need_to_save = True
        if 'max_experience' in request.data:
            queryset.max_experience = request.data['max_experience']
            need_to_save = True
        if 'job_location' in request.data:
            queryset.job_location = request.data['job_location']
            need_to_save = True
        if 'min_budget' in request.data:
            queryset.min_budget = request.data['min_budget']
            need_to_save = True
        if 'max_budget' in request.data:
            queryset.max_budget = request.data['max_budget']
            need_to_save = True
        if 'notice_period' in request.data:
            queryset.notice_period = request.data['notice_period']
            need_to_save = True
        if 'score' in request.data:
            queryset.score = request.data['score']
            need_to_save = True
        if 'actor' in request.data :
            request.data['actor']= request.auth.user.id
            queryset.actor = request.data['actor']
            need_to_save = True
        if need_to_save:
            queryset.save()
        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Successfully Updated"}, status=status.HTTP_200_OK )


    @auth_cls
    def retrieve(self, request, *args, **kwargs):
        """
            GET /requirement/{id}
            Response Type - JSON
            List Of Particular Requirements By ID
        """
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()
        self.serializer_class = RequirementSerializer
        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Success"}, status=status.HTTP_200_OK )

    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /requirement/{id}
            Response Type - JSON
            Deleting A Requirements
        """
        # self.queryset = Requirement.objects.filter()
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()
        queryset.delete()
        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Deleted Successfully"}, status=status.HTTP_200_OK )




class UploadDetails(viewsets.GenericViewSet):
    queryset = Upload.objects.filter()
    serializer_class = UploadSerializer

    @auth_cls
    def list(self, request,*args, **kwargs):
        """
            GET /upload/
            Response Type - JSON
            List Of Uploads
        """
        request.data['actor'] = request.auth.user.id
        queryset = self.get_queryset()
        queryset= queryset.filter(actor=request.auth.user)
        serializer = UploadSerializer(queryset, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Uploaded Files"}, status=status.HTTP_200_OK )

    @auth_cls
    def create(self, request,*args, **kwargs):
        """
            POST /upload/
            Response Type - JSON
            User Can Upload files bulk or single,store & updates credits in usercredits available&upoad credits
        """
        resp= []
        for each in request.FILES.getlist('files[]'):
            uploaded_file = each
            print(uploaded_file)
            util.save(uploaded_file)
            uploaded_file= str(uploaded_file)
            file_path = util.file_path(uploaded_file)
            file_name = util.file_name(uploaded_file)
            # file_extension=util.file_name(uploaded_file)
            file_size = util.file_size(uploaded_file)
            file_extension = util.file_extension(uploaded_file)
            assigned_name = util.assigned_name()
            actor= request.auth.user.id
            credit = [2,3,4,5,6,7,8,9]
            score= random.choice(credit)
            data={'actor':actor,'filepath':file_path,'original_name':file_name,'filesize':file_size,'extension':file_extension,'system_name':assigned_name,'score':score}
            user_queryset = self.get_serializer(data=data)
            user_queryset.is_valid(raise_exception=True)
            user_queryset.save()
            resp.append(user_queryset.data)

            user_credit= UserCredit.objects.filter(actor=request.auth.user)
            if user_credit.count():
                user_credit= user_credit[0]
                user_credit.available_credit= Decimal(user_credit.available_credit) + Decimal(score)
                # user_credit.available_credit= "%.2f" % available_credit
                user_credit.upload_credit= Decimal(user_credit.upload_credit) + Decimal(score)
                # user_credit.upload_credit= "%.2f" % upload_credit
                user_credit.save()
            user_upload= Upload.objects.filter(actor=actor)
            if user_upload.count():
                user_upload= user_upload[0]
                transaction_history= TransactionHistory.objects.create(actor=request.auth.user,upload_id= user_upload,action= 'credit',amount= score)
                account_details= AccountDetails.objects.create(actor=request.auth.user,upload_id= user_upload)

        return response.Response({'result':resp, 'message':"Successfully Uploaded"}, status=status.HTTP_200_OK)

    @auth_cls
    def retrieve(self, request, *args, **kwargs):
        """
            GET /upload/{id}
            Response Type - JSON
            Retrieves a Uploaded File by id
        """
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()
        self.serializer_class = UploadSerializer
        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"Success"}, status=status.HTTP_200_OK )   

    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /upload/{id}
            Response Type - JSON
            Deletes a Uploaded File by id
        """
        request.data['actor'] = request.auth.user.id
        queryset = self.get_object()
        os.remove(queryset.filepath)
        queryset.delete()
        return response.Response({'message':"Deleted Successfully"}, status=status.HTTP_200_OK)



@decorators.api_view(['GET'])
@auth
def purchase(request):
    data= request.data
    file_id= request.GET.get('id')
    request.data['actor'] = request.auth.user.id
    if not file_id:
        return response.Response({'message':"Please Provide Proper File ID"}, status=status.HTTP_400_BAD_REQUEST)
    user_requirement= Requirement.objects.filter(actor=request.auth.user.id)
    if user_requirement.count():
        user_requirement= user_requirement[0]
    user_upload= Upload.objects.filter(id=file_id)
    if user_upload.count():
        user_upload= user_upload[0]
        score= user_upload.score
    user_credit= UserCredit.objects.filter(actor=request.auth.user.id)
    if user_credit.count():
        user_credit= user_credit[0]
        if user_credit.available_credit >= score:
            user_credit.available_credit= Decimal(user_credit.available_credit) - Decimal(score)
            # user_credit.available_credit= "%.2f" % available_credit
            user_credit.download_credit= Decimal(user_credit.download_credit) + Decimal(score)
            # user_credit.upload_credit= "%.2f" % upload_credit
            user_credit.save()
            token= secrets.token_urlsafe(50)
            transaction_history= TransactionHistory.objects.create(actor= request.auth.user,amount= score,action='debit',download_token= token,requirement_id=user_requirement,upload_id=user_upload)
            serializer= TransactionHistorySerializer(transaction_history)
            return response.Response({'result':serializer.data,'message':"Successfully Purchased"}, status=status.HTTP_200_OK)
        else:
            return response.Response({'message':"Your Credits Are Low,Please Upload Files"}, status=status.HTTP_400_BAD_REQUEST)


mime= magic.Magic(mime=True)
@decorators.api_view(['GET'])
# @auth
def downloads(request):
    """
        GET /filedownload/{id}
        Response Type - JSON
        File Download
    """
    data = request.data
    file_id = request.GET.get('auth', None)
    if not file_id:
        return response.Response("Provide Access Key", status=status.HTTP_400_BAD_REQUEST)
    transaction_history= TransactionHistory.objects.filter(download_token=file_id)
    if transaction_history.count():
        transaction_history= transaction_history[0]
    file_path= transaction_history.upload_id.filepath
    with open(file_path,'rb') as fp:
        output = HttpResponse(fp.read(),content_type = mime.from_file(file_path))
        output['Content-Disposition'] = 'attachment; filename="filename"'
    return  output



@decorators.api_view(['GET'])
# @auth
def file_view(request):
    """
        GET /filedownload/{id}
        Response Type - JSON
        File Preview in the browser
    """
    data = request.data
    file_id = request.GET.get('auth', None)
    if not file_id:
        return response.Response("Provide Access Key", status=status.HTTP_400_BAD_REQUEST)
    transaction_history= TransactionHistory.objects.filter(download_token=file_id)
    if transaction_history.count():
        transaction_history= transaction_history[0]
    file_path= transaction_history.upload_id.filepath

    with open(file_path,'rb') as fp:
        response = HttpResponse(fp.read(),content_type = mime.from_file(file_path))
        response['Content-Disposition'] = 'inline; filename="file.docx"'
        return response


@decorators.api_view(['GET'])
@auth
def user_credit(request):
    request.data['actor']= request.auth.user.id
    user_credit= UserCredit.objects.filter(actor=request.auth.user)
    if user_credit.count():
        user_credit= user_credit[0]
        
        serializer= UserCreditSerializer(user_credit)
    return response.Response({'result':serializer.data,'message':"Current Available Score"}, status=status.HTTP_200_OK ) 



@decorators.api_view(['POST'])
def forgot_password_email(request):
    data = request.data
    email = data['email']
    user= User.objects.filter(email= email)
    if not user.count():
        return response.Response({'message':"Please provide proper email"}, status=status.HTTP_400_BAD_REQUEST)
    token = secrets.token_urlsafe(20)
    user_token= UserToken.objects.filter(user= user[0])
    if user_token.count():
        user_token= user_token[0]
        user_token.token= token
        user_token.save()
        url= 'http://127.0.0.1:8001/forgotpassword/?token='+str(token)+'&user='+data['email']
        forgot(data['email'],url)
        return response.Response({'message':"Please Verify Email For Forgot Password Link"}, status=status.HTTP_200_OK)


@decorators.api_view(['POST'])
def forgot_password(request):
    data= request.data
    token = request.GET.get('token')
    email = request.GET.get('user')

    user = User.objects.filter(email = email)
    if not user.count():
        return response.Response({'message':"Please provide proper email"}, status=status.HTTP_400_BAD_REQUEST)
    user_token = UserToken.objects.filter(user = user[0])
    # user_token = user_token[]
    if user_token.count():
        user_secret = UserSecret.objects.filter(user = user[0])
        # user_secret = user_secret[0]
    if user_secret.count():
        user_secret = user_secret[0]
        user_secret.password = make_password(data['password'])
        user_secret.save()
        return response.Response({'message':"Successfully Password Created"}, status=status.HTTP_200_OK)
    return response.Response({'message':"Please provide Proper Details"}, status=status.HTTP_400_BAD_REQUEST)



@decorators.api_view(['POST'])
@auth
def admin_block(request):
    data= request.data
    user= request.auth.user.id
    user_secret= UserSecret.objects.filter(user= user,is_admin= True,is_blocked=False)
    if user_secret.count():
        user_secret= user_secret[0]
    else:
        return response.Response({'message':'You Are Not Admin To Access'}, status=status.HTTP_401_UNAUTHORIZED)
    user_secret= UserSecret.objects.filter(user=data['user'])
    if 'is_blocked' in request.data:
        if request.data['is_blocked'] == 'True':
            if user_secret.count():
                user_secret=user_secret[0]
                user_secret.is_blocked= True
                user_secret.save()
                return response.Response({'message':"Your Account Has Blocked"}, status=status.HTTP_200_OK)
        else:
            if request.data['is_blocked'] == 'False':

                if user_secret.count():
                    user_secret=user_secret[0]
                    user_secret.is_blocked= False
                    user_secret.save()
                    return response.Response({'message':"Your Account Has Un_Blocked"}, status=status.HTTP_401_UNAUTHORIZED)
    

@decorators.api_view(['GET'])
@auth
def requirement_matched_files(request):
    request.data['actor']= request.auth.user.id
    user_requirement= Requirement.objects.filter(actor= request.auth.user)
    if user_requirement.count():
        user_requirement= user_requirement[0]
    user_upload= Upload.objects.exclude(actor= request.auth.user.id)
    transaction_history= TransactionHistory.objects.exclude(actor= request.auth.user.id,)

    return response.Response(UploadSerializer(user_upload, many=True).data)