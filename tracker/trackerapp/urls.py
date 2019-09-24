from django.conf.urls import url, include
from trackerapp import views
from rest_framework import routers
from django.contrib import admin
from django.conf import settings
# from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register('userauth', views.UserAuthViewSet) # User CRUD
router.register('projects', views.ProjectsViewSet) # User ProjectDetails CRUD
router.register('versions',views.ProjectVersionsViewSet)
router.register('projectusers',views.ProjectUsersViewSet)

 
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'login', views.user_login), #  User Login 
    url(r'user_confirmation/',views.user_confirmation), # User Confirmation with email-linlk
    url(r'logout', views.user_logout), # User Logout
    url(r'changepassword', views.change_password), # Login User Change Password
    url(r'forgotpasswordemail/',views.password),#forgot password with email link
    url(r'forgot/password/',views.forgot_password),#user Forgot password
    url(r'projectnames',views.search),#user Forgot password
    url(r'emails',views.searchemail),#user Forgot password
    url(r'useradd',views.user_add),
    url(r'names',views.usernames),
    url(r'proname',views.searchprojects),
    url(r'projectversion',views.project_versions),
    url(r'details',views.project_details),
    url(r'userprojects',views.user_projects),
    url(r'userdelete',views.user_delete),
    url(r'nameproject',views.projectssearch),
    url(r'normaluser',views.normal_user_add),
    url(r'prover',views.searchversions),
    url(r'jobchoices',views.job_choices),
    url(r'userblock',views.admin_block),




    ]

# ]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

