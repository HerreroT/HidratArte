from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User

class AuthTests(APITestCase):
    def setUp(self):
    
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            address="123 test street"
        )

    def test_login_successful(self):
        url = reverse('login')
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_login_failed(self):
        url = reverse('login')
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        # Primero logueamos
        self.client.login(username="testuser", password="testpass123")
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout exitoso')

    def test_register_user(self):
        url = reverse('users-list')  
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "address": "some address"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


