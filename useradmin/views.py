from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializer import UserSerializer
from .permissons import IsAdminOrReadOnly

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]


@method_decorator(csrf_exempt, name='dispatch')  # <- solo si tenés errores de CSRF
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Crea la sesión
            return Response({
                "message": "Login exitoso",
                "username": user.username,
                "email": user.email,
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)


