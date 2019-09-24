from rest_framework import serializers
from . models import User,Projects,ProjectVersions,ProjectUsers
from rest_framework.serializers import ValidationError
from trackerapp import util


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__' 

class UserResponseSerializer(serializers.ModelSerializer):
    id=serializers.ReadOnlyField()
    name=serializers.ReadOnlyField()
    email=serializers.ReadOnlyField()
    class Meta:
        model=User
        fields=('id','name','email')

class ProjectsSerializer(serializers.ModelSerializer):
    created_by= UserResponseSerializer()
    id=serializers.ReadOnlyField()
    project_name=serializers.ReadOnlyField()

    class Meta:
        model = Projects
        fields = ('id', 'project_name', 'created_by','versions')

class ProjectsNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = ('id', 'project_name')


class ProjectVersionsSerializer(serializers.ModelSerializer):
    project= ProjectsNameSerializer()

    class Meta:
        model = ProjectVersions
        fields =('id','repo_url','repo_username','repo_password','repo_branch','status', 'project','postman_link','is_hosted','hosted_username',\
            'hosted_password','hosted_ip_address','application_url','application_username','application_password','application_user_type','version','created_by','updated_by', 'members')
class UserVersionsSerializer(serializers.ModelSerializer):
    project= ProjectsNameSerializer()

    class Meta:
        model = ProjectVersions
        fields =('id','repo_url','repo_username','repo_branch','status', 'project','postman_link','is_hosted','hosted_username',\
            'hosted_ip_address','application_url','application_username','application_user_type','version','created_by','updated_by', 'members')


class ProjectVersionsResponseSerializer(serializers.ModelSerializer):    
    id = serializers.ReadOnlyField()
    project = ProjectsSerializer()
    repo_url = serializers.ReadOnlyField()
    repo_username = serializers.ReadOnlyField()
    repo_password = serializers.ReadOnlyField()
    repo_branch = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    postman_link = serializers.ReadOnlyField()
    is_hosted = serializers.ReadOnlyField()
    hosted_username = serializers.ReadOnlyField()
    hosted_password = serializers.ReadOnlyField()
    hosted_ip_address = serializers.ReadOnlyField()
    application_username = serializers.ReadOnlyField()
    application_url = serializers.ReadOnlyField()
    application_password = serializers.ReadOnlyField()
    application_user_type = serializers.ReadOnlyField()
    version = serializers.ReadOnlyField()
    role = serializers.ReadOnlyField()
    created_by = UserResponseSerializer()
    updated_by = UserResponseSerializer()

    class Meta:
        model = ProjectVersions
        fields =('id','repo_url','repo_username','repo_password','repo_branch','status', 'project','postman_link','is_hosted','hosted_username',\
            'hosted_password','hosted_ip_address','application_url','application_username','application_password','application_user_type','version','role','created_by','updated_by', 'members')

class VersionsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    version=serializers.ReadOnlyField()
    class Meta:
        model=Projects
        fields=('id','version')

class ProjectUsersSerializer(serializers.ModelSerializer):
    user= UserResponseSerializer()
    project= ProjectsNameSerializer()
    version= VersionsSerializer()

    class Meta:
        model = ProjectUsers
        fields = '__all__'

class TestSerializer(serializers.ModelSerializer):
    project= ProjectsNameSerializer()
    version= ProjectVersionsSerializer()
    class Meta:
        model = ProjectUsers
        fields = '__all__'

class ProjectsResponseSerializer(serializers.ModelSerializer):    
    id = serializers.ReadOnlyField()
    project_name = serializers.ReadOnlyField()
    created_by = UserResponseSerializer()
    updated_by = UserResponseSerializer()
    class Meta:
        model=Projects
        fields=('id','project_name', 'versions', 'created_by', 'updated_by','members') 