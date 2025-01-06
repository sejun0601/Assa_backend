from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import Profile

from django.contrib.auth import get_user_model, logout, authenticate , login
from .serializers import RegisterSerializer, ProfileSerializer
from django.middleware.csrf import get_token


User = get_user_model()

class GoogleLoginView(APIView):
    def post(self, request, *args, **kwargs):
        id_token_str = request.data.get("id_token")
        if not id_token_str:
            return Response({"detail": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                "839534423473-gr7ketdfqujrem8ur9tjtgu1h4p8728s.apps.googleusercontent.com"
            )
            email = idinfo.get('email')

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # User를 DB에서 조회 혹은 생성
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(username=email, email=email)

        login(request, user)

        return Response({"detail": "Login successful"}, status=status.HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"detail": "회원가입 성공", "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 세션에 사용자 정보 저장
            login(request, user)
            return Response({"detail": "로그인 성공"}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "로그인 실패"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)

class LoginStatusView(APIView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({
                "logged_in": True,
                "username": request.user.username,
                "email":request.user.email
            }, status=200)
        return Response({
            "logged_in": False
        }, status=200)
        
class CSRFTokenView(APIView):
    """
    CSRF 토큰을 반환하는 View
    """
    def get(self, request, *args, **kwargs):
        csrf_token = get_token(request)
        return Response({"csrfToken": csrf_token}, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 현재 로그인된 사용자와 연결된 프로필 가져오기
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=200)