from django.urls import reverse
from rest_framework import status

from task_tracker.test import TestCase
from task_tracker.apps.users.factories import UserFactory


class TestAuthentication(TestCase):

    def setUp(self):
        super().setUp()
        self.api_client.logout()

        self.regular_user = UserFactory()
        self.raw_password = 'testpassword123'
        self.regular_user.set_password(self.raw_password)
        self.regular_user.save()

        # Endpoints
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_token_obtain(self):
        """Test obtaining JWT token with valid credentials."""
        response = self.api_client.post(
            self.token_url,
            {
                'username': self.regular_user.username,
                'password': self.raw_password
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        self.assertTrue(len(response.data['access']) > 20)
        self.assertTrue(len(response.data['refresh']) > 20)

    def test_token_obtain_invalid_credentials(self):
        """Test obtaining JWT token with invalid credentials."""
        response = self.api_client.post(
            self.token_url,
            {
                'username': self.regular_user.username,
                'password': 'wrongpassword'
            }
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'No active account found with the given credentials')

    def test_token_refresh(self):
        """Test refreshing an access token using a refresh token."""
        response = self.api_client.post(
            self.token_url,
            {
                'username': self.regular_user.username,
                'password': self.raw_password
            }
        )
        refresh_token = response.data['refresh']

        refresh_response = self.api_client.post(
            self.refresh_url,
            {'refresh': refresh_token}
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertTrue(len(refresh_response.data['access']) > 20)

    def test_token_refresh_invalid(self):
        """Test refreshing with an invalid refresh token."""
        response = self.api_client.post(
            self.refresh_url,
            {'refresh': 'invalid.refresh.token'}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint(self):
        """Test accessing a protected endpoint with and without a token."""
        response = self.api_client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        token_response = self.api_client.post(
            self.token_url,
            {
                'username': self.regular_user.username,
                'password': self.raw_password
            }
        )
        access_token = token_response.data['access']

        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        auth_response = self.api_client.get("/api/users/")
        self.assertNotEqual(auth_response.status_code, status.HTTP_401_UNAUTHORIZED)
