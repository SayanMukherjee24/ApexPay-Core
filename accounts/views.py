# Django imports
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.conf import settings

# App imports
from accounts.services import create_user_wallet
from accounts.tokens import account_activation_token
from accounts.serializers import (
    ResetSerializer,
    UserSerailizer,
    LoginSerializer,
    ResetPasswordSeriliazer
)
from accounts.models import User

# rest_framework imports
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


# -------------------------------------------------------------------------
# REGISTER USER
# -------------------------------------------------------------------------

class Register(GenericAPIView):
    serializer_class = UserSerailizer
    
    def post(self, request, format='json'):
        # Check existing user
        num_results = User.objects.filter(email=request.data["email"]).count()
        if num_results > 0:
            return Response(
                {"message": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            user.is_active = False
            user.save()

            # ⭐ BUILD ACTIVATION LINK USING settings.SITE_DOMAIN ⭐
            activation_link = (
                f"{settings.SITE_DOMAIN}/api/v1/auth/confirm-email/"
                f"{urlsafe_base64_encode(force_bytes(str(user.pk)))}/"
                f"{account_activation_token.make_token(user)}"
            )

            subject = "Activate your account"
            message = (
                f"Hi, {user.first_name} {user.last_name}!\n\n"
                "Please click the link below to activate your account:\n\n"
                f"{activation_link}\n\n"
                "Thank you for using our application!"
            )

            from_email = settings.EMAIL_HOST_USER or "no-reply@example.com"
            send_mail(subject, message, from_email, [user.email])

            return Response(
                {"message": "User created successfully. Check your email."},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"message": "User already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# -------------------------------------------------------------------------
# LOGIN USER
# -------------------------------------------------------------------------

class Login(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            return Response(
                {"message": "Email or password is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if check_password(data["password"], user.password):
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "message": "Login Successful",
                        "data": {
                            "user": {
                                "user_id": user.pk,
                                "email": user.email,
                            },
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    }
                )

            return Response(
                {"message": "User is not active"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"message": "Email or password is incorrect"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


# -------------------------------------------------------------------------
# RESEND ACTIVATION LINK
# -------------------------------------------------------------------------

class ResendActivationLink(GenericAPIView):
    serializer_class = ResetSerializer

    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({"message": "User is already active"}, status=status.HTTP_400_BAD_REQUEST)

        activation_link = (
            f"{settings.SITE_DOMAIN}/api/v1/auth/confirm-email/"
            f"{urlsafe_base64_encode(force_bytes(str(user.pk)))}/"
            f"{account_activation_token.make_token(user)}"
        )

        subject = "Activate your account"
        message = (
            f"Hi, {user.first_name} {user.last_name}!\n\n"
            "Please click the link below to activate your account:\n\n"
            f"{activation_link}\n\nThank you for using our application!"
        )

        from_email = settings.EMAIL_HOST_USER or "no-reply@example.com"
        send_mail(subject, message, from_email, [user.email])

        return Response({"message": "Email sent"}, status=status.HTTP_200_OK)


# -------------------------------------------------------------------------
# ACTIVATE EMAIL
# -------------------------------------------------------------------------

class ActivateEmail(GenericAPIView):
    swagger_schema = None
    swagger_fake_view = True
    serializer_class = None

    def get(self, request, user_id, token):
        try:
            user_id = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            create_user_wallet(user)
            return Response({"message": "Email activated successfully"}, status=status.HTTP_200_OK)

        return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------------
# RESET PASSWORD EMAIL
# -------------------------------------------------------------------------

class ResetPassword(GenericAPIView):
    serializer_class = ResetSerializer

    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "User does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response(
                {"message": "User is not active. Request an activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_link = (
            f"{settings.SITE_DOMAIN}/api/v1/auth/reset-password-confirm/"
            f"{urlsafe_base64_encode(force_bytes(str(user.pk)))}/"
            f"{account_activation_token.make_token(user)}"
        )

        subject = "Reset Your Password"
        message = (
            f"Hi, {user.first_name} {user.last_name}!\n\n"
            "Click below to reset your password:\n\n"
            f"{reset_link}\n\n"
        )

        from_email = settings.EMAIL_HOST_USER or "no-reply@example.com"
        send_mail(subject, message, from_email, [user.email])

        return Response({"message": "Check your mail to reset your password"}, status=status.HTTP_200_OK)


# -------------------------------------------------------------------------
# CONFIRM PASSWORD RESET
# -------------------------------------------------------------------------

class ConfirmPassword(GenericAPIView):
    serializer_class = ResetPasswordSeriliazer

    def put(self, request, user_id, token):
        try:
            user_id = force_str(urlsafe_base64_decode(user_id))
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if not account_activation_token.check_token(user, token):
            return Response({"message": "Password Reset Failed!"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user.set_password(request.data.get("password"))
            user.save()
            return Response({"message": "New password set."}, status=status.HTTP_200_OK)

        return Response({"data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------------
# LOGOUT
# -------------------------------------------------------------------------

class Logout(GenericAPIView):
    swagger_schema = None
    swagger_fake_view = True
    serializer_class = None

    def post(self, request):
        logout(request)
        return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)


# -------------------------------------------------------------------------
# USER PROFILE (JWT REQUIRED)
# -------------------------------------------------------------------------

class Profile(GenericAPIView):
    swagger_schema = None
    swagger_fake_view = True
    serializer_class = None
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
