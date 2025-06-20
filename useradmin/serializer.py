from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'address']
        extra_kwargs = {
            'password': {'write_only': True}  # Para que no se devuelva la password en la respuesta
        }

    def create(self, validated_data):
        password = validated_data.pop('password')  # Saca la password del dict
        user = User(**validated_data)
        user.set_password(password)  # Genera el hash de la contraseña
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Si hay una nueva contraseña, la hashea
        instance.save()
        return instance
