from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'address']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class EmailLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("username")  # viene del frontend como "username"
        password = attrs.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email incorrecto.")

        if not user_obj.check_password(password):
            raise serializers.ValidationError("Contraseña incorrecta.")

        attrs["username"] = user_obj.username  # necesario para que SimpleJWT funcione
        return super().validate(attrs)
