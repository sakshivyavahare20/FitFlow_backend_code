from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializer import Userserializer, UserserializerWithToken
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import status
 
# for sending mails and generate token
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from .utils import TokenGenerator,generate_token
from django.utils.encoding import force_bytes,force_text,DjangoUnicodeDecodeError
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.generic import View

# View for returning basic routes
def getRoutes(request):
    return JsonResponse("Hi, welcome to the API", safe=False)


# Custom Token Serializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserserializerWithToken(self.user).data
        for key, value in serializer.items():
            data[key] = value
        return data


# Custom Token View
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# User Profile View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    serializer = Userserializer(user, many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    users=User.objects.all()
    serializer=Userserializer(users,many=True)
    return Response(serializer.data)
@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        # Check if a user with the given email already exists
        if User.objects.filter(email=data['email']).exists():
            return Response({'details': "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a user with the given username already exists
        if User.objects.filter(username=data['username']).exists():
            return Response({'details': "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user with is_active set to False
        user = User.objects.create_user(
            username=data['username'],  # Ensure a unique username is provided
            email=data['email'],       # Ensure a unique email is provided
            password=data['password'], # Password will be hashed
            is_active=False
        )

        # Generate the activation email content
        email_subject = "Activate Your Account"
        message = render_to_string(
            "activate.html",
            {
                'user': user,
                'domain': '127.0.0.1:8000',  # Replace with your domain in production
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generate_token.make_token(user)
            }
        )

        # Send the activation email
        email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [data['email']])
        email_message.send()

        # Serialize the user data
        serialize = UserserializerWithToken(user, many=False)
        return Response(serialize.data)

    except Exception as e:
        print(f"Error: {e}")
        return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    
from django.shortcuts import render, redirect

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            # Decode the user ID from the activation link
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        # Validate the token
        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, "activatesuccess.html")  # Successful activation template
        else:
            return render(request, "activatefail.html")  # Failed activation template
