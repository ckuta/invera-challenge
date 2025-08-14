from django.test import (
    TestCase as BaseTestCase,
    TransactionTestCase as BaseTransactionTestCase,
)
from task_tracker.apps.users.factories import AdminUserFactory
from rest_framework.test import APIClient


class TestCaseMixin:
    fixtures = []

    def setUp(self):
        super().setUp()

        self.user = AdminUserFactory(username='admin')
        self.api_client = APIClient()
        self.api_client.force_authenticate(self.user)


class TestCase(TestCaseMixin, BaseTestCase): ...
