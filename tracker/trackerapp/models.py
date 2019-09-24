"""
Django imported packages
"""
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.core.validators import EmailValidator,URLValidator
from django.contrib.postgres.fields import ArrayField
"""
3rd party packages imported
"""
import uuid

JOB_CHOICES = (
        ('BACK-END_DEVELOPER','BACK-END_DEVELOPER'),
        ('FRONT-END_DEVELOPER','FRONT-END_DEVELOPER'),
        ('TEAM_LEAD','TEAM_LEAD'),
        ('PROJECT_MANAGER','PROJECT_MANAGER'),
        ('CEO','CEO'),
        ('CTO','CTO'),
        ('DEVOPS','DEVOPS'),
        ('DATA_OPERATORS','DATA_OPERATORS'),
        ('DATA_SCIENTIST','DATA_SCIENTIST'),
        ('MANUAL_TESTER','MANUAL_TESTER'),
        ('AUTOMATION_TESTER','AUTOMATION_TESTER'),
        ('SENIOR_BACK-END_DEVELOPER', 'SENIOR_BACK-END_DEVELOPER'),
        ('FULL_STACK_DEVELOPER', 'FULL_STACK_DEVELOPER'),
        ('SENIOR_FRONT-END_DEVELOPER', 'SENIOR_FRONT-END_DEVELOPER'),
        ('SYSTEM_ADMIN', 'SYSTEM_ADMIN'),
        ('LEAD_DATA_SCIENTIST','LEAD_DATA_SCIENTIST')
    )



class AbstractBaseClass(models.Model):
    """
    ClassName AbstractBaseClass
    FieldName UUID
    For generating Unique Id Field
    It stores user details of every Catalogue Users like Guest_user,registered_user etc 
    """

    id= models.UUIDField( 
        primary_key= True,
        default= uuid.uuid4,
        editable= False
    )
    created_at= models.DateTimeField(default=timezone.now)
    updated_at= models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True


class User(AbstractBaseClass):
    """
    ClassName User
    It stores user details of every Catalogue Users 
    Data like Username and Email are here 
    """ 
    USER_CHOICES = (
    ('ADMIN','ADMIN'),
    ('USER','USER'),
    )                                          
    name= models.CharField(max_length=255,null=True)
    email= models.EmailField(
        unique=True,
        max_length=255,
        validators=[EmailValidator()],
        )
    designation= models.CharField(
        max_length=255,
        choices=JOB_CHOICES,
    
        )
    user_type= models.CharField(max_length=255,choices=USER_CHOICES,default="USER")
    phone_number= models.CharField(unique=True,max_length=10,null=True)
    joined_on= models.DateTimeField(default=timezone.now)
    password= models.TextField(max_length=255,null=True)#stores the password in encrypted form
    reset_code= models.TextField(max_length=255,null=True)# unique token generated for the Catalogue Users
    token= models.TextField(max_length=255,null=True)# unique token generated for the Catalogue Users
    is_active= models.BooleanField(default=False)# To check the user in active state or not
    is_blocked= models.BooleanField(default=True)# To check the user is blocked or not

    class Meta:
        db_table= 'users'
        ordering= ['-updated_at']


class Projects(AbstractBaseClass):
    """
    ClassName UserSecret
    For Storing the user account details of Catalogue
    Data like Password and others are here
    """  

    project_name= models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='project_created_fk'
            )
    updated_by = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='project_updated_fk'
            )

    class Meta:
        db_table='user_projects'
        ordering=['-updated_at']

    @property
    def members(self):
        from trackerapp.models import ProjectUsers
        from trackerapp.serializers import ProjectUsersSerializer
        return ProjectUsersSerializer(ProjectUsers.objects.filter(project=self), many=True).data
    
    @property
    def versions(self):
        from trackerapp.models import ProjectVersions
        from trackerapp.serializers import ProjectVersionsSerializer
        return ProjectVersionsSerializer(ProjectVersions.objects.filter(project=self), many=True).data
    


class ProjectVersions(AbstractBaseClass):

    STATUS_CHOICES = (
        ('Requirement Gathering','Requirement Gathering'),
        ('Development','Development'),
        ('Testing','Testing'),
        ('Staging','Staging'),
        ('Ready For Production','Ready For Production'),
        ('Moved To Production','Moved To Production'),
        ('Refactory','Refactory'),
        ('Rewriting','Rewriting'),
        ('Parked','Parked'),

    )
    created_by = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='user_created_fk'
            )
    updated_by = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='user_updated_fk'
            )
    project = models.ForeignKey(
            Projects,
            on_delete=models.CASCADE,
            related_name='user_projects_fk') 

    repo_url = models.URLField(max_length= 255)
    repo_username = models.TextField(max_length=255)
    repo_password = models.TextField(max_length=255)
    repo_branch = models.TextField(max_length=255)
    is_hosted = models.BooleanField(default=False)
    hosted_username = models.TextField(max_length=255,null=True)
    hosted_password = models.TextField(max_length=255,null=True)
    hosted_ip_address = models.TextField(max_length=255,null=True)
    application_url = models.TextField(max_length=255,null=True)
    application_username = models.TextField(max_length=255,null=True)
    application_password = models.TextField(max_length=255,null=True)
    application_user_type = models.TextField(max_length=255,null=True)
    postman_link = models.URLField(max_length= 255,null=True)
    status = models.TextField(max_length=255, choices=STATUS_CHOICES)
    version= models.TextField(max_length=100)
    
    class Meta:
        db_table='project_versions'
        ordering=['-updated_at']
        unique_together = [['project', 'version']]

    @property
    def members(self):
        from trackerapp.models import ProjectUsers
        from trackerapp.serializers import ProjectUsersSerializer
        return ProjectUsersSerializer(ProjectUsers.objects.filter(version=self), many=True).data



class ProjectUsers(AbstractBaseClass):    
    role= models.CharField(max_length=255,
        choices=JOB_CHOICES
        )
    user= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='userid_fk',   
        )
    project= models.ForeignKey(
        Projects,
        on_delete=models.CASCADE,
        related_name='projectid_fk',
        )
    version= models.ForeignKey(
        ProjectVersions,
        on_delete=models.CASCADE,
        related_name= 'version_fk',
        )
    class Meta:
        db_table='project_users'
        ordering=['-updated_at']
        unique_together = [['version', 'user']]
