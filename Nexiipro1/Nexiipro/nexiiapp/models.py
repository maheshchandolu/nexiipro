"""
Django imported packages
"""
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
"""
3rd party packages imported
"""
import uuid



class AbstractBaseClass(models.Model):
    """
    ClassName AbstractBaseClass
    FieldName UUID
    For generating Unique Id Field
    It stores user details of every CVBANK Users like Guest_user,registered_user etc 
    """                                       
    id= models.UUIDField( 
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at= models.DateTimeField(default=timezone.now)
    updated_at= models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True


class UserType(AbstractBaseClass):
    """
    ClassName UserType
    It stores user details of Type of user of CVBANK etc 
    """ 
    user_types= (
        (1,'member'),
        (2,'company'),
    )
    user_type= models.PositiveSmallIntegerField(choices=user_types,default=1)
    
    class Meta:
    	db_table = 'user_type'
    	ordering = ['-updated_at']


class User(UserType):
    """
    ClassName User
    It stores user details of every CVBANK Users 
    Data like Username and Email are here 
    """                                               
    user_name= models.CharField(max_length=255)
    email= models.EmailField(unique=True,null=True) 

    class Meta:
        db_table='users'
        ordering=['-updated_at']


class UserSecret(AbstractBaseClass):
    """
    ClassName UserSecret
    For Storing the user account details of CVBANK
    Data like Password and others are here
    """                                           
    display_name= models.CharField(max_length=255,null=True)
    user= models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='user_secret_user_fk'
        )
    password= models.TextField(max_length=255,null=True)#stores the password in encrypted form
    reset_code= models.TextField(max_length=255,null=True)# unique token generated for the CVBANK Users
    is_active= models.BooleanField(default=False)# To check the user in active state or not
    is_blocked= models.BooleanField(default=True)# To check the user is blocked or not
    is_admin= models.BooleanField(default=False)# To check whether the user is an admin or not

    class Meta:
        db_table='user_secrets'
        ordering=['-updated_at']


class UserToken(AbstractBaseClass):
    """
    ClassName UserToken
    It stores user login access token and its expire time.
    """
    token= models.CharField(max_length=255)
    expired_at= models.DateTimeField(default=timezone.now)
    browser_agent= models.CharField(max_length=255,null=True)# used to maintain the tracking of Guest users
    user= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='usertoken_actor',
    )


    class Meta:
        db_table='usertoken'
        ordering=['updated_at']


class Requirement(AbstractBaseClass):
    """
    ClassName Requirement
    It stores the details of the Requirement posted by the CVBANK user.
    Data like technical_skills,experience and others are here

    """         
    technical_skills= JSONField()
    job_role= models.CharField(max_length=255) # Used to store profile_type(examples=Developer,Tester,Teamlead)
    min_experience= models.DecimalField(decimal_places=2, max_digits=3)
    max_experience= models.DecimalField(decimal_places=2, max_digits=3)
    job_location= models.CharField(max_length=255,null=True) # This field is used to store the prefered Job Location                     
    min_budget= models.PositiveIntegerField(null=True) # Used to maintain the accuracy in fetching profiles
    max_budget= models.PositiveIntegerField(null=True)
    notice_period= models.DecimalField(decimal_places=2,max_digits=3,null=True)  
    score= models.DecimalField(decimal_places=2, max_digits=20, default=0) # To store the credit score for posted requirement 
    actor= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requirement_actor',
        blank = True,
    )

    class Meta:
        db_table='requirements'
        ordering=['-updated_at']


class Upload(AbstractBaseClass):
    """
    ClassName Upload
    It stores the details of the uploaded profiles.
    Data like System name,filepath,score and others are here.
    """                                                    
    system_name= models.CharField(max_length=255) # Store the profile name in the format of DDMMYYHHMMSS
    original_name= models.CharField(max_length=255)
    filepath= models.TextField() # Store the path/location where the uploaded profiles will be stored 
    extension= models.CharField(max_length=255) # Store the extension of uploaded file (eg=pdf,doc,docx..) 
    filesize= models.CharField(max_length=255) # Store the size of uploaded file in bytes
    score= models.DecimalField(decimal_places=2, max_digits=20, default=0) # Store the credit score of the uploaded files
    actor= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploads_actor'
    )

    class Meta:
        db_table='uploads'
        ordering=['-updated_at']


class UserCredit(AbstractBaseClass):
    """
    ClassName UserCredit
    It stores details of the available credits of the CVBANK users.
    Data like user and Available credits are here.
    """
    actor= models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='user_credit_user'
    )
    upload_credit= models.DecimalField(decimal_places=2, max_digits=20, default=0)
    download_credit= models.DecimalField(decimal_places=2, max_digits=20, default=0)
    available_credit= models.DecimalField(decimal_places=2, max_digits=20, default=0)

    def save(self, *args, **kwargs):
        # print (self.available_credit, *args)
        self.available_credit= self.available_credit
        self.upload_credit= self.upload_credit
        self.download_credit= self.download_credit
        super(UserCredit, self).save(*args, **kwargs)

    class Meta:
        db_table='user_credit'
        ordering=['-updated_at']


class TransactionHistory(AbstractBaseClass):
    """
    ClassName TransactionHistory
    It stores details of user Transactions like how many credits debited and how many credted.
    Data like action(credit and debit) and others are here.
    """
    actor= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_transactions'
    )
    action= models.CharField(max_length=200)# used to store whether score is credited or debited

    upload_id= models.ForeignKey(
        Upload,
        on_delete=models.CASCADE,
        related_name='transaction_upload_id',
        null= True
    )# used for store the id of uploaded files
    requirement_id= models.ForeignKey(
        Requirement,
        on_delete=models.CASCADE,
        related_name='transaction_requirement_id',
        null= True
    )# used to store id of dowloads-requirement
    amount= models.DecimalField(decimal_places=2, max_digits=15, default=0)# to store debit and credit scores
    download_filename= models.CharField(max_length=255,null=True)
    download_token= models.CharField(max_length=255,null=True)
    download_count= models.PositiveIntegerField(default=0)

    class Meta:
        db_table='user_transactions'
        ordering=['-updated_at']


class AccountDetails(AbstractBaseClass):  
    """
    ClassName AccountDetails
    It stores the details of user account history like for a requirement what are the profiles uploaded and what are the profiles downloaded
    Data like Requirement_id and Upload_id are here
    """          
    requirement_id= models.ForeignKey(
        Requirement,
        on_delete=models.CASCADE,
        related_name='user_requirement_id',
        null= True
    )#used to store the id of requirement posted
    upload_id= models.ForeignKey(       
        Upload,
        on_delete=models.CASCADE,
        related_name='account_upload_id',
        null= True
    ) # used to store id of uploaded files
    actor= models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='account_actor',
    )

    class Meta:
        db_table='user_account_details'
        ordering=['-updated_at']

# Create your models here.

