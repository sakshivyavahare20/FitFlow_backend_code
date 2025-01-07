from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
class Userserializer(serializers.ModelSerializer):
    name=serializers.SerializerMethodField(read_only=True)
    _id=serializers.SerializerMethodField(read_only=True)
    isAdmin=serializers.SerializerMethodField(read_only=True)
   
    class Meta:
        model=User
        fields=['id','_id','username','email','isAdmin']
    
    # def get_name(self,obj):
    #     firstname=obj.first_name
    #     lastname=obj.last_name
    #     name=firstname+' '+lastname
    #     if name=='':
    #         name=obj.email[:5]
    #         return name
    #     return name
    
    def get__id(self,obj):
        return obj.id

    def get_isAdmin(self,obj):
        return obj.is_staff
    
    
class UserserializerWithToken(Userserializer):
    token=serializers.SerializerMethodField(read_only=True)
    class Meta:
        model=User
        fields=['id','_id','username','email','isAdmin','token']
    
    def get_token(self,obj):
        token=RefreshToken.for_user(obj)
        return str(token.access_token)