from rest_framework import serializers
from . models import User, Requirement,Upload,UserType,UserSecret,UserToken,UserCredit,AccountDetails,TransactionHistory
from rest_framework.serializers import ValidationError
from nexiiapp import util


class UserTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserType
        fields = '__all__' 


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class UserSecretSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSecret
        fields = '__all__'


class UserTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserToken
        fields = '__all__'


class RequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Requirement
        fields = '__all__'


class UploadSerializer(serializers.ModelSerializer):
	
	class Meta:
		model = Upload
		fields='__all__'


class UserCreditSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserCredit
        fields = '__all__'


class TransactionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TransactionHistory
        fields = '__all__'


class AccountDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountDetails
        fields = '__all__'
