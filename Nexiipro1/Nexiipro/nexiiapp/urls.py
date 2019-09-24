from django.conf.urls import url, include
from nexiiapp import views
from rest_framework import routers
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register('userauth', views.UserAuthViewSet) # User CRUD
router.register('requirement', views.RequirementViewSet) # User Requirement CRUD
router.register('upload', views.UploadDetails) # User Upload CRUD except update 



urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'login', views.user_login), #  User Login 
    url(r'cvbank/v1/user_confirmation/',views.user_confirmation), # User Confirmation with email-linlk
    url(r'logout', views.user_logout), # User Logout
    url(r'changepassword', views.change_password), # Login User Change Password
    url(r'filedownload',views.downloads), # User File Download 
    url(r'fileview',views.file_view), # User Fileview
    url(r'usercredit',views.user_credit),
    url(r'forgotpassword/email',views.forgot_password_email),
    url(r'forgotpassword',views.forgot_password),
    url(r'adminblock',views.admin_block),
    url(r'reqmatchedfiles',views.requirement_matched_files),
    url(r'filepurchase',views.purchase),





]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)






    
