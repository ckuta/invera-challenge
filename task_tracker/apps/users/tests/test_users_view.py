from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

from task_tracker.test import TestCase
from task_tracker.apps.users.factories import UserFactory

User = get_user_model()


class TestUserViews(TestCase):
    def setUp(self):
        super().setUp()

        self.regular_user = UserFactory()
        self.regular_password = 'testpassword123'
        self.regular_user.set_password(self.regular_password)
        self.regular_user.save()

        self.another_user = UserFactory()

        self.staff_user = UserFactory(is_staff=True, is_superuser=False)

        self.inactive_user = UserFactory(is_active=False)

        self.register_url = reverse('user-register-list')
        self.users_list_url = reverse('user-list-list')

        # Helper method to get profile URL for a specific user
        def get_profile_url(user_id):
            return reverse('user-profile-detail', kwargs={'pk': user_id})

        self.get_profile_url = get_profile_url

    def test_create_user_happy_path(self):
        """Test successfully creating a new user."""
        new_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongP@ssword123',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], new_user_data['username'])
        self.assertEqual(response.data['email'], new_user_data['email'])
        self.assertEqual(response.data['first_name'], new_user_data['first_name'])
        self.assertEqual(response.data['last_name'], new_user_data['last_name'])

        self.assertNotIn('password', response.data)

        self.assertTrue(User.objects.filter(username=new_user_data['username']).exists())

    def test_create_user_weak_password(self):
        """Test creating a user with a weak password that fails validation."""
        new_user_data = {
            'username': 'weakpassuser',
            'email': 'weak@example.com',
            'password': 'password',
            'first_name': 'Weak',
            'last_name': 'Password'
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_create_user_short_password(self):
        """Test creating a user with a password that's too short."""
        new_user_data = {
            'username': 'shortpassuser',
            'email': 'short@example.com',
            'password': 'Sh0rt!',
            'first_name': 'Short',
            'last_name': 'Password'
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_create_user_numeric_password(self):
        """Test creating a user with an entirely numeric password."""
        new_user_data = {
            'username': 'numericpassuser',
            'email': 'numeric@example.com',
            'password': '12345678',
            'first_name': 'Numeric',
            'last_name': 'Password'
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_create_user_validation_errors(self):
        """Test that validation errors provide sufficient information."""
        new_user_data = {
            'username': '',
            'email': 'not-an-email',
            'password': 'short'
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check for specific validation messages
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_list_users_as_admin(self):
        """Test that admin users can see all users including inactive ones."""
        self.api_client.logout()
        self.api_client.force_authenticate(self.user)

        response = self.api_client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        total_users = User.objects.count()
        self.assertEqual(response.data['count'], total_users)

        inactive_user_ids = list(User.objects.filter(is_active=False).values_list('id', flat=True))
        response_user_ids = [user['id'] for user in response.data['results']]

        for user_id in inactive_user_ids:
            self.assertIn(user_id, response_user_ids)

    def test_list_users_as_regular_user(self):
        """Test that regular users can only see their own details."""
        self.api_client.logout()
        self.api_client.force_authenticate(self.regular_user)

        response = self.api_client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)

        user_data = response.data['results'][0]
        self.assertEqual(user_data['id'], self.regular_user.id)
        self.assertEqual(user_data['username'], self.regular_user.username)
        self.assertEqual(user_data['email'], self.regular_user.email)

    def test_user_created_as_active(self):
        """Test that newly created users are active by default."""
        new_user_data = {
            'username': 'activeuser',
            'email': 'active@example.com',
            'password': 'StrongP@ssword123',
            'first_name': 'Active',
            'last_name': 'User',
        }

        response = self.api_client.post(self.register_url, new_user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username=new_user_data['username'])
        self.assertTrue(created_user.is_active)

    def test_regular_user_cannot_delete_others(self):
        """Test that a regular user cannot delete other users."""
        self.api_client.force_authenticate(self.regular_user)

        response = self.api_client.delete(self.get_profile_url(self.another_user.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.another_user.id).exists())

    def test_regular_user_can_delete_self(self):
        """Test that a regular user can delete themselves."""
        self.api_client.force_authenticate(self.regular_user)

        # Delete self
        response = self.api_client.delete(self.get_profile_url(self.regular_user.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

    def test_admin_can_delete_any_user(self):
        """Test that an admin user can delete any user."""
        self.api_client.force_authenticate(self.user)

        response = self.api_client.delete(self.get_profile_url(self.regular_user.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

        response = self.api_client.delete(self.get_profile_url(self.staff_user.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.staff_user.id).exists())

    def test_regular_user_cannot_escalate_privileges(self):
        """Test that a regular user cannot escalate their own privileges."""
        self.api_client.force_authenticate(self.regular_user)

        # Try to make self an admin
        escalated_data = {
            'is_staff': True,
            'is_superuser': True
        }

        response = self.api_client.patch(self.get_profile_url(self.regular_user.id), escalated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.regular_user.refresh_from_db()

        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)

    def test_update_password(self):
        """Test updating a user's password."""
        self.api_client.force_authenticate(self.regular_user)

        password_data = {
            'password': 'NewStrongP@ssword456'
        }

        response = self.api_client.patch(self.get_profile_url(self.regular_user.id), password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.api_client.logout()

        login_data = {
            'username': self.regular_user.username,
            'password': 'NewStrongP@ssword456'
        }

        login_response = self.api_client.post('/api/token/', login_data)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)

    def test_regular_user_cannot_view_other_profiles(self):
        """Test that regular users cannot view profiles of other users."""
        self.api_client.force_authenticate(self.regular_user)

        response = self.api_client.get(self.get_profile_url(self.another_user.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_view_own_profile(self):
        """Test that regular users can view their own profile."""
        self.api_client.force_authenticate(self.regular_user)

        response = self.api_client.get(self.get_profile_url(self.regular_user.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)

    def test_staff_can_view_any_profile(self):
        """Test that staff users can view any user profile."""
        self.api_client.force_authenticate(self.staff_user)

        response = self.api_client.get(self.get_profile_url(self.regular_user.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)

        response = self.api_client.get(self.get_profile_url(self.inactive_user.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.inactive_user.username)

    def test_filter_users_by_username(self):
        """Test that users can be filtered by username."""
        self.api_client.force_authenticate(self.staff_user)

        specific_user = UserFactory(username="target_username")
        response = self.api_client.get(
            self.users_list_url, {'username': 'target_username'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        result_user = response.data['results'][0]
        self.assertEqual(result_user['username'], specific_user.username)

    def test_filter_users_by_email(self):
        """Test that users can be filtered by email."""
        self.api_client.force_authenticate(self.staff_user)

        specific_user = UserFactory(email="target@example.com")
        response = self.api_client.get(
            self.users_list_url, {'email': 'target@example.com'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        result_user = response.data['results'][0]
        self.assertEqual(result_user['email'], specific_user.email)