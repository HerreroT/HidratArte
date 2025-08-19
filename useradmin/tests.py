from rest_framework.test import APITestCase
from django.urls import reverse
from .models import User
from rest_framework import status

class JWTAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jwtuser",
            email="jwt@mail.com",
            password="jwtpass123",
            address="JWT st."
        )

    def test_obtain_token(self):
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {"username": "jwtuser", "password": "jwtpass123"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_access_protected_view(self):
        token_resp = self.client.post(reverse('token_obtain_pair'),
                                      {"username": "jwtuser", "password": "jwtpass123"}, format='json')
        access = token_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get(reverse('profile'))   # ruta de ProfileView
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_refresh_token(self):
        token_resp = self.client.post(reverse('token_obtain_pair'),
                                      {"username": "jwtuser", "password": "jwtpass123"}, format='json')
        refresh = token_resp.data['refresh']
        resp = self.client.post(reverse('token_refresh'), {"refresh": refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
