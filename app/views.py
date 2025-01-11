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

from django.core.validators import validate_email
from django.core.exceptions import ValidationError


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


# # User Profile View
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def getUserProfile(request):
#     user = request.user
#     serializer = Userserializer(user, many=False)
#     return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAdminUser])
# def getUsers(request):
#     users=User.objects.all()
#     serializer=Userserializer(users,many=True)
#     return Response(serializer.data)

import re
from django.core.exceptions import ValidationError

def validate_password(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")

def validate_username(username):
    if len(username) < 4 or len(username) > 20:
        raise ValidationError("Username must be between 4 and 20 characters.")
    if not re.match(r"^[A-Za-z0-9_-]+$", username):
        raise ValidationError("Username can only contain letters, digits, underscores, and hyphens.")
    if not any(char.isupper() for char in username):
        raise ValidationError("Username must contain at least one uppercase letter.")

@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        # Validate username and password
        validate_username(data['username'])
        validate_password(data['password'])

        # Check if password and confirm password match
        if data['password'] != data.get('confirm_password', ''):
            return Response({'details': "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        try:
            validate_email(data['email'])
        except ValidationError:
            return Response({'details': "Enter a valid email address."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if username or email already exists
        if User.objects.filter(username=data['username']).exists():
            return Response({'details': "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=data['email']).exists():
            return Response({'details': "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user with `is_active` set to False
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
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
        try:
            email_message = EmailMessage(
                subject=email_subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[data['email']]
            )
            email_message.content_subtype = "html"  # Ensure the email is sent as HTML
            email_message.send()
        except Exception as mail_error:
            print(f"Mail Error: {mail_error}")
            return Response({'details': "Failed to send activation email. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Serialize and return user data
        serializer = UserserializerWithToken(user, many=False)
        return Response(serializer.data)

    except ValidationError as ve:
        return Response({'details': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
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


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def logoutUser(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
    except KeyError:
        return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
