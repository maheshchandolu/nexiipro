from django.shortcuts import render

# Create your views here.

import secrets, os, magic, random
from . import models
from nexiiapp.models import User, Requirement, Upload, UserSecret, UserToken, UserCredit, UserType, TransactionHistory, AccountDetails
from rest_framework import viewsets, response, decorators, status
from rest_framework.decorators import action
from . serializers import UserSerializer, RequirementSerializer, UploadSerializer, UserTypeSerializer, UserSecretSerializer
from . serializers import UserCreditSerializer, TransactionHistorySerializer, AccountDetailsSerializer, UserTokenSerializer
from django.contrib.auth.hashers import make_password, check_password
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.serializers import ValidationError
from nexiiapp import util
from nexiiapp.util import send, auth, auth_cls,forgot
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
        # request.data['actor'] = request.auth.user.id
        queryset = self.get_queryset()
        print(queryset)
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
        user = User.objects.create(user_name = data['user_name'],email = data['email'])
        user_token = UserToken.objects.create(token = token,user = user)
        user_credit = UserCredit.objects.create(actor = user)
        transaction_history = TransactionHistory.objects.create(actor=user)
        accout_details = AccountDetails.objects.create(actor = user)
        user_secret = UserSecret.objects.create(user = user)
        user_admin= UserSecret.objects.filter(user=user)
        if 'is_admin' in request.data:
            if user_admin.count():
                user_admin=user_admin[0]
                user_admin.is_admin=data['is_admin']
                user_admin.save()
        user_queryset=UserSerializer(user)
        url= 'http://127.0.0.1:8000/cvbank/v1/user_confirmation/?token='+str(token)+'&user='+data['email']
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
        request.data['actor'] = request.auth
        queryset = self.get_object()
        self.serializer_class = UserSerializer

        serializer = self.get_serializer(queryset)
        return response.Response({'result':serializer.data,'message':"User Successfully Retrived"},status=status.HTTP_200_OK )

    @auth_cls
    def delete(self, request, *args, **kwargs):
        """
            DELETE /userauth/{id}
            Response Type - JSON
            DELETE  UserBy ID

        """
        request.data['actor'] = request.auth.user.id
        self.queryset = User.objects.filter()
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
    
    print(user,'====')
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
                else:
                    return request.Response({'message':"Your Account is Deactivated"}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return request.Response({'message':"Please Activate Your Account"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer= UserSecretSerializer(user_secret)
            return response.Response({'result':serializer.data, 'message': "You Are Successfully SignedIn"}, status=status.HTTP_200_OK)
        return response.Response({'message':"Email/Password are required Fields"}, status=status.HTTP_401_UNAUTHORIZED)
    return response.Response({'message':"Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)


# @decorators.api_view(['POST'])
# def guest_login(request):
#     data = request.data
#     if 'temp_auth_id' in request.data:
#         # import pdb;pdb.set_trace()
#         user = User.objects.filter(user_name= data['temp_auth_id'])
#         if user.count():
#             # print()
#             user=user[0]
#             reset_code = secrets.token_urlsafe(20)
#             user = UserSecret.objects.filter(user=user)
#             print(user)
#             user=UserSecret.objects.create(reset_code=reset_code)
#             user.save()
#             serializer= UserSecretSerializer(user)
#             return response.Response({'result': serializer.data, 'message': "You Are Successfully SignedIn"}, status=status.HTTP_200_OK)
    

#     reset_code = secrets.token_urlsafe(20)
#     user = User.objects.create(user_name=data['temp_auth_id'])
#     user = UserSecret.objects.create(user=user,is_active=True,is_blocked=False,reset_code=reset_code) 
#     serializer= UserSecretSerializer(user)
#     return response.Response({'result': serializer.data, 'message': "created and logged in"},status=status.HTTP_200_OK)



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
    print(email)

    user = User.objects.filter(email = email)
    print(user[0].email)
    if not user.count():
        return response.Response('Please provide proper email')
    user_token = UserToken.objects.filter(user = user[0])
    # user_token = user_token[]
    print(user_token)
    if user_token.count():
        user_secret = UserSecret.objects.filter(user = user[0])
        print(user_secret)
        # user_secret = user_secret[0]
    if user_secret[0].is_active:
        return response.Response('User is Already Activated')
    if user_secret.count():
        user_secret = user_secret[0]
        user_secret.password = make_password(data['password'])
        user_secret.is_active = True
        user_secret.is_blocked = False
        user_secret.save()
        return response.Response('Successfully Created')
    return response.Response('Please provide Proper Details')
    #     user_secret.save()


    # # print(user_token[0].token)
    # # print(user_secret[0].is_active)

    # if not user_secret.count():
    #     return response.Response({'message':"Acitivation Link Has Expired"}, status=status.HTTP_400_BAD_REQUEST)
    # if user_secret[0].is_active:
    #     return response.Response({'message':"Already User Has Acitivated"}, status=status.HTTP_201_CREATED)

    # user= UserSecretSerializer(user_secret)
    # user.password = make_password(data['password'])
    # # user.token = None
    # user.is_active = True
    # user.is_blocked = False
    # if user.is_valid():
    #     user.save()

    # return response.Response({'message':"Successfully SignedIn"}, status=status.HTTP_200_OK)


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
        return response.Response({'message':"Please Provide Password"}, status=status.HTTP_400_BAD_REQUEST)

    if 'newpassword' not in data:
        return response.Response({'message':"Please Provide NewPassword"}, status=status.HTTP_400_BAD_REQUEST)

    if 're-newpassword' not in data:
        return response.Response({'message':"Please Provide Re-NewPassword"}, status=status.HTTP_400_BAD_REQUEST)
        
    userdetails= request.auth.reset_code
    print(userdetails,'==========email===========')

    user= UserSecret.objects.filter(reset_code= userdetails)
    # user_token = UserToken.objects.filter(user = user[0])
    # user_secret = UserSecret.objects.filter(user = user[0])

    if user.count():
        user= user[0]
    else:
        return response.Response({'message':"User Not Found"}, status=status.HTTP_400_BAD_REQUEST)

    if check_password(data['password'], user.password):

        if 'password' in request.data:
            if user.is_active:            
                if request.data['newpassword'] != request.data['re-newpassword']:
                    return response.Response({'message':"Please Provide Same Password"}, status=status.HTTP_400_BAD_REQUEST)
                else:                
                    user.password = make_password(data['newpassword'])  
                    user.save()
                    serializer= UserSecretSerializer(user)

            return response.Response({ 'result':serializer.data,'message': "Your Password Changed Successfully"}, status=status.HTTP_200_OK)
        else:
            return response.Response({'message':"Your Account is InActive"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return response.Response({'message':"Please Provide Previous Password"}, status=status.HTTP_400_BAD_REQUEST)



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
        print(queryset,'------------requirements-----------')
        queryset = queryset.filter(actor=request.auth.user)

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
        credit=[1,2,3,4,5,6,7,8,9]
        request.data['score']=random.choice(credit)
        print(request.data['score'])
        # print(request.auth.user.id,'------calling------')
        user_queryset = self.get_serializer(data=request.data)
        user_queryset.is_valid(raise_exception=True)
        # user_queryset.actor =
        user_queryset.save()
        # print(user_queryset.data.get('id'))

        # import pdb;pdb.set_trace()
        # req_obj=user_queryset.data.filter(id=id)
        # req_obj=req_obj[0]
        # print(req_obj)
        Req=Requirement.objects.filter(actor=request.auth.user)
        if Req.count():
            Req=Req[0]
            accout_details=AccountDetails.objects.create(actor=request.auth.user,requirement_id=Req)
            transaction_history=TransactionHistory.objects.create(actor=request.auth.user,requirement_id=Req,action='debit',amount=request.data['score'])
        # transaction_history=transaction_history[0]
        # transaction_history.requirement_id=user_queryset.data.get('id')
        # transaction_history.save()

        # req_id.requirement_id=user_queryset.id
        # req_id.save()
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
        queryset = queryset.filter(actor=request.auth.user)
        print(queryset,"======uploads===========")
        serializer = UploadSerializer(queryset, many=True)
        return response.Response({'result':serializer.data,'message':"List Of Uploaded Files"}, status=status.HTTP_200_OK )

    @auth_cls
    def create(self, request,*args, **kwargs):
        """
            POST /upload/
            Response Type - JSON
            User Can Upload files bulk or single
        """
        resp= []
        for each in request.FILES.getlist('files[]'):
            uploaded_file = each
            util.save(uploaded_file)
            uploaded_file= str(uploaded_file)
            file_path = util.file_path(uploaded_file)
            file_name = util.file_name(uploaded_file)
            # file_extension=util.file_name(uploaded_file)
            file_size = util.file_size(uploaded_file)
            file_extension = util.file_extension(uploaded_file)
            system_name = util.assigned_name()
            actor= request.auth.user.id
            credit = [2,3,4,5,6,7,8,9]
            score= random.choice(credit)
            



            data={'actor':actor,'filepath':file_path,'original_name':file_name,'filesize':file_size,'extension':file_extension,'system_name':system_name,'score':score}
            user_queryset = self.get_serializer(data=data)
            user_queryset.is_valid(raise_exception=True)
            user_queryset.save()
            resp.append(user_queryset.data)

            # trans=TransactionHistory.objects.filter(actor=actor)
            # print(trans)
            # trans=upload_id[0]
            # trans.upload_id=user_queryset.id
            # tras.save()

            # ad=AccountDetails.objects.filter(actor=actor)
            # print(ad)
            # ad.requirement_id=user_queryset.id
            # ad.save()
            user_credit=UserCredit.objects.filter(actor=actor)
            if user_credit.count():
                user_credit=user_credit[0]
                user_credit.available_credit=user_credit.available_credit+score
                user_credit.upload_credit=user_credit.upload_credit+score
                user_credit.save()
                print(type(user_credit.available_credit),type(score))


            upload=Upload.objects.filter(actor=actor)

            if upload.count():
                upload=upload[0]

                print(upload,'+++++++')

                accout_details=AccountDetails.objects.create(actor=request.auth.user,upload_id=upload)

                transaction_history=TransactionHistory.objects.create(actor=request.auth.user,upload_id=upload,action='credit',amount=score)



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


    def options(self,request):
        pass


mime= magic.Magic(mime=True)
@decorators.api_view(['GET'])
@auth
def downloads(request):
    """
        GET /filedownload/{id}
        Response Type - JSON
        File Download
    """
    data=request.data
    file_id=request.GET.get('id')
    print(file_id)
    request.data['actor'] = request.auth.user.id
    # request.data['id']=id
    # print(id,'===========id=======')
    Req=Requirement.objects.filter(actor=request.auth.user)
    if Req.count():
        Req=Req[0]


    user_uploads= Upload.objects.exclude(actor=request.auth.user)
    print(user_uploads)
    # print(user_requirement,"------actor------")
    for each in user_uploads:

        score= each.score
        file_id=each.id
        print(file_id,"=====",score)
        # print(score,"----_SCore-----------")

        user_credit= UserCredit.objects.filter(actor=request.auth.user)
        if user_credit.count():
            user_credit= user_credit[0]
            if user_credit.available_credit > score:

                user_credit.available_credit= user_credit.available_credit-score
                # user_credit.available_credit= "%.2f" % available_credit
                user_credit.download_credit=user_credit.download_credit+score
                # user_credit.upload_credit= "%.2f" % upload_credit
                user_credit.save()
            else:
                return response.Response({'message':"Your Credits Are Low,Please Upload Files"})

        # user_credit=UserCredit.objects.filter(actor=request.auth.user)
        # user_credit=user_credit[0]
        # user_credit.available_credit=user_credit.available_credit-score
        # user_credit.download_credit=user_credit.downlaod_credit+score
        # user_credit.save()
        # print(type(user_credit.available_credit),type(score))



            files=Upload.objects.filter(id=file_id)


            print(files,'=======123======')
            if files.count():
                files=files[0]
                # import pdb;pdb.set_trace()
                # print(files['file_path'],"=====file=====")
                file_path=files.filepath
                # print(file_path)
                # file_name=files.file_name
                # print(file_name)
                # extension=files.file_extension
                # print(extension)
                file_path=str(file_path)
                print(file_path,'lllllllllll')
                
                # file_path = settings.MEDIA_ROOT+"/cat.pdf"
                # print(file_path,'======filepath====')
                # content_type=mime.from_file(file_path)
                # print(content_type)
                with open(file_path,'rb') as fp:
                    res = HttpResponse(fp.read(),content_type = mime.from_file(file_path))

                    res['Content-Disposition'] = 'attachment; filename="filename"'
                return res
        # return HttpResponse({'message':"Downloaded Successfully"}, status=status.HTTP_200_OK)




@decorators.api_view(['GET'])
@auth
def file_view(request):
    """
        GET /filedownload/{id}
        Response Type - JSON
        File Preview in the browser
    """
    file_path = settings.MEDIA_ROOT+'/cat.pdf'
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
    return response.Response({'result':serializer.data,'message':"Success"}, status=status.HTTP_200_OK )

    
@decorators.api_view(['POST'])
def password(request):
    data = request.data
    
    email = data['email']
   
    user = User.objects.filter(email = email)
    if not user.count():
        return response.Response('Email Doesnot Exist')
    token = secrets.token_urlsafe(20)
    user_token=UserToken.objects.filter(user=user[0])
    if user_token.count():
        user_token=user_token[0]
        user_token.token=token
        user_token.save()
        url= 'http://127.0.0.1:8000/forget/password/?token='+str(token)+'&user='+data['email']
        forgot(data['email'],url)
        return response.Response("Forgot Password Link has been Sent to your Email")


@decorators.api_view(['POST'])
def forget_password(request):
    # token = secrets.token_urlsafe(20)

    data= request.data
    token = request.GET.get('token')
    email = request.GET.get('user')
    print(email)

    user = User.objects.filter(email = email)
    print(user[0].email)
    if not user.count():
        return response.Response('Please provide proper email')
    user_token = UserToken.objects.filter(user = user[0])
    # user_token = user_token[]
    print(user_token)
    if user_token.count():
        user_secret = UserSecret.objects.filter(user = user[0])
        print(user_secret)
        # user_secret = user_secret[0]
    if user_secret.count():
        user_secret = user_secret[0]
        user_secret.password = make_password(data['newpassword'])
        user_secret.save()
        return response.Response('Password Changed Succcessfully')
    return response.Response('Please provide Proper Details')
# @decorators.api_view(['GET'])
# @auth
# def transaction_history(request):
#     request.data['actor']= request.auth.user.id
#     user_requirement= Requirement.objects.filter(actor=request.auth.user)
#     # if user_requirement.count():
#         # requirement= user_requirement[0]
#         user_transactions=TransactionHistory.objects.filter(actor=request.auth.user_requirement[0])
#         user_transactions=user_transactions[0]
#         if user
#     else:
#         return response.Response({'message':"user requirement doesn't exist's "})   
#     score1= requirement.score

#     user_upload= Upload.objects.filter(actor=request.auth.user)

#     # if not user_upload.count():
#     #     return response.Response({'message':"user uploads doesn't exist's "})
#     score2=0
#     for upload in user_upload:
#         score2+= upload.score

#     transaction_history= TransactionHistory.objects.filter(actor=request.auth.user)
#     if transaction_history.count():
#         transaction_history= transaction_history[0]
@decorators.api_view(['GET'])
@auth
def requirement_matched_profiles(request):
    request.data['actor']= request.auth.user
    user_requirement= Requirement.objects.filter(actor= request.auth.user)
    if user_requirement.count():
        user_requirement= user_requirement[0]
    user_upload= Upload.objects.exclude(actor= request.auth.user.id)
    print(user_upload,"########")
    serializer= UploadSerializer(user_upload,many=True)
    print(serializer,"---------serializer")

    # data= {'system_name':assigned_name,'score':score}
    return response.Response(serializer.data)
