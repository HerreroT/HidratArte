from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import User
from .serializer import UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import EmailLoginSerializer

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "address": user.address,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser
        })

    def patch(self, request):
        user = request.user
        data = request.data

        username = data.get('username', user.username)
        email = data.get('email', user.email)
        address = data.get('address', user.address)

        # Basic validation: email uniqueness
        if email != user.email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return Response({'email': 'Este email ya está en uso.'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = username
        user.email = email
        user.address = address

        # Optional password change: expects 'current_password' and 'new_password'
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if current_password or new_password:
            if not current_password or not new_password:
                return Response({'password': 'Se requieren current_password y new_password para cambiar la contraseña.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(current_password):
                return Response({'password': 'Contraseña actual incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)

        user.save()

        return Response({
            'username': user.username,
            'email': user.email,
            'address': user.address,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })

class LogoutJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout exitoso"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailLoginSerializer
