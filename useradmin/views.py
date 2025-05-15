from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializer import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LoginView(APIView):
    def post(self, request):
        name = request.data.get("name")
        password = request.data.get("password")

        try:
            user = User.objects.get(name=name, password=password)
            return Response({
                "message": "Login exitoso",
                "username": user.name,
                "email": user.email,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)


