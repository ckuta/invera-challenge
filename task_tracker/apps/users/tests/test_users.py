import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from task_tracker.apps.users.factories import UserFactory, AdminUserFactory


class TestUserModel(TestCase):
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username="admin_user",
            email="admin_user@example.com",
            password="adminpass123"
        )

        self.assertEqual(admin.username, "admin_user")
        self.assertEqual(admin.email, "admin_user@example.com")
        self.assertTrue(admin.check_password("adminpass123"))
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_factory(self):
        """Test that the UserFactory works correctly."""
        user = UserFactory()

        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)
        self.assertTrue(user.check_password("password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_admin_factory(self):
        """Test that the AdminUserFactory works correctly."""
        admin = AdminUserFactory()

        self.assertIsNotNone(admin.username)
        self.assertIsNotNone(admin.email)
        self.assertTrue(admin.check_password("password"))
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_factory_custom_attributes(self):
        """Test creating a user with custom attributes via factory."""
        custom_user = UserFactory(
            username="custom",
            email="custom@example.com"
        )

        self.assertEqual(custom_user.username, "custom")
        self.assertEqual(custom_user.email, "custom@example.com")
        self.assertTrue(custom_user.check_password("password"))

    def test_user_permissions(self):
        """Test user permissions."""
        user = UserFactory()
        admin = AdminUserFactory()

        # Admin should have more permissions than regular user
        self.assertTrue(admin.has_perm("auth.add_user"))
        self.assertTrue(admin.has_perm("auth.change_user"))
        self.assertTrue(admin.has_perm("auth.delete_user"))

        self.assertFalse(user.has_perm("auth.add_user"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))