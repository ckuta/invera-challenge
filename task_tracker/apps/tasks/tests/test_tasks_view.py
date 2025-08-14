from datetime import timedelta

from task_tracker.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.utils import timezone

from task_tracker.apps.tasks.models import Task
from task_tracker.apps.tasks.factories import TaskFactory, UserFactory


class TaskViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.normal_user = UserFactory()
        self.other_user = UserFactory()

    def test_user_can_create_task(self):
        """Test an user can create a task"""
        TaskFactory(user=self.normal_user)

        self.api_client.force_authenticate(user=self.normal_user)
        data = {
            'description': 'This is a new task description',
            'completed': False
        }

        response = self.api_client.post(reverse('task-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.last().user, self.normal_user)

    def test_api_throws_errors_on_bad_requests(self):
        """Test the API throws errors on bad create/update/delete requests"""
        self.api_client.force_authenticate(user=self.normal_user)
        task = TaskFactory(user=self.normal_user, description="Test task description")

        # Bad create
        data = {'description': ''}
        response = self.api_client.post(reverse('task-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        # Bad update
        data = {'description': ''}
        response = self.api_client.patch(
            reverse('task-update-description', kwargs={'pk': task.id}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_see_task_they_dont_own(self):
        """Test a user that does not own a task cannot see it"""
        task = TaskFactory(user=self.normal_user)

        self.api_client.force_authenticate(user=self.other_user)
        response = self.api_client.get(
            reverse('task-detail', kwargs={'pk': task.id}),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_task_they_dont_own(self):
        """Test a user that does not own a task cannot update it"""
        task = TaskFactory(user=self.normal_user, description="Some description")

        self.api_client.force_authenticate(user=self.other_user)
        data = {'description': 'Updated description'}
        response = self.api_client.patch(
            reverse('task-update-description', kwargs={'pk': task.id}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_task_they_dont_own(self):
        """Test a user that does not own a task cannot delete it"""
        task = TaskFactory(user=self.normal_user)

        self.api_client.force_authenticate(user=self.other_user)
        response = self.api_client.delete(
            reverse('task-delete', kwargs={'pk': task.id}),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_all_tasks(self):
        """Test listing all tasks for the authenticated user"""
        # Create multiple tasks for the user
        TaskFactory.create_batch(5, user=self.normal_user)
        TaskFactory.create_batch(3, user=self.other_user)  # Other user's tasks

        self.api_client.force_authenticate(user=self.normal_user)
        response = self.api_client.get(reverse('task-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see only their own tasks (5 + 1 from setUp)
        self.assertEqual(len(response.data['results']), 5)

    def test_list_view_is_paginated(self):
        """Test the list view is paginated"""
        TaskFactory.create_batch(15, user=self.normal_user)  # Create 15 more tasks

        self.api_client.force_authenticate(user=self.normal_user)
        response = self.api_client.get(reverse('task-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

    def test_description_is_truncated_in_list(self):
        """Test description is truncated to 50 chars in list view"""
        long_description = "This is a very long description that should be truncated in the list view. It's definitely longer than 50 characters."
        task = TaskFactory(user=self.normal_user, description=long_description)

        self.api_client.force_authenticate(user=self.normal_user)
        response = self.api_client.get(reverse('task-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the task in the response
        task_in_response = next(
            (item for item in response.data['results'] if item['id'] == task.id),
            None
        )

        self.assertIsNotNone(task_in_response)
        self.assertEqual(len(task_in_response['description']), 53)
        self.assertTrue(task_in_response['description'].endswith('...'))

    def test_filter_by_exact_description(self):
        """Test filtering tasks by exact description match."""
        task1 = TaskFactory(user=self.normal_user, description="Buy groceries")
        task2 = TaskFactory(user=self.normal_user, description="Buy new laptop")
        task3 = TaskFactory(user=self.normal_user, description="Call plumber")

        self.api_client.force_authenticate(user=self.normal_user)

        response = self.api_client.get(reverse('task-list') + '?description=Buy groceries')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.api_client.get(reverse('task-list') + '?description=buy groceries')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.api_client.get(reverse('task-list') + '?description=Nonexistent task')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_by_description_contains(self):
        """Test filtering tasks where description contains a substring."""
        task1 = TaskFactory(user=self.normal_user, description="Buy groceries")
        task2 = TaskFactory(user=self.normal_user, description="Buy new laptop")
        task3 = TaskFactory(user=self.normal_user, description="Call plumber")
        task4 = TaskFactory(user=self.normal_user, description="groceries shopping list")

        self.api_client.force_authenticate(user=self.normal_user)

        response = self.api_client.get(reverse('task-list') + '?description__contains=groceries')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(task1.id, result_ids)
        self.assertIn(task4.id, result_ids)

        response = self.api_client.get(reverse('task-list') + '?description__contains=GROCERIES')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        response = self.api_client.get(reverse('task-list') + '?description__contains=Buy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(task1.id, result_ids)
        self.assertIn(task2.id, result_ids)

    def test_filter_by_description_startswith(self):
        """Test filtering tasks where description starts with a specific prefix."""
        task1 = TaskFactory(user=self.normal_user, description="Buy groceries")
        task2 = TaskFactory(user=self.normal_user, description="Buy new laptop")
        task3 = TaskFactory(user=self.normal_user, description="Call plumber")
        task4 = TaskFactory(user=self.normal_user, description="buy medicine")  # Lowercase "buy"

        self.api_client.force_authenticate(user=self.normal_user)

        response = self.api_client.get(reverse('task-list') + '?description__startswith=Buy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)  # Should match all 3 tasks starting with "Buy"/"buy"

        response = self.api_client.get(reverse('task-list') + '?description__startswith=buy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.api_client.get(reverse('task-list') + '?description__startswith=Call')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task3.id)

    def test_filter_by_description_regex(self):
        """Test filtering tasks where description matches a regex pattern."""
        task1 = TaskFactory(user=self.normal_user, description="Buy groceries")
        task2 = TaskFactory(user=self.normal_user, description="Buy new laptop")
        task3 = TaskFactory(user=self.normal_user, description="Call plumber")
        task4 = TaskFactory(user=self.normal_user, description="Email the client")
        task5 = TaskFactory(user=self.normal_user, description="Read book")

        self.api_client.force_authenticate(user=self.normal_user)

        response = self.api_client.get(reverse('task-list') + '?description__regex=er$')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1, response.data)
        self.assertEqual(response.data['results'][0]['id'], task3.id)

        response = self.api_client.get(reverse('task-list') + '?description__regex=^(Buy|Call)')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(task1.id, result_ids)
        self.assertIn(task2.id, result_ids)
        self.assertIn(task3.id, result_ids)

        response = self.api_client.get(reverse('task-list') + '?description__regex=^buy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_combined_description_and_completion_filters(self):
        """Test combining description filters with completion status."""
        task1 = TaskFactory(user=self.normal_user, description="Buy groceries", completed=True)
        task2 = TaskFactory(user=self.normal_user, description="Buy new laptop", completed=False)
        task3 = TaskFactory(user=self.normal_user, description="Call plumber", completed=True)
        task4 = TaskFactory(user=self.normal_user, description="buy medicine", completed=False)

        self.api_client.force_authenticate(user=self.normal_user)

        response = self.api_client.get(reverse('task-list') + '?description__contains=Buy&completed=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.api_client.get(reverse('task-list') + '?description__startswith=Buy&completed=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(task2.id, result_ids)
        self.assertIn(task4.id, result_ids)

        response = self.api_client.get(reverse('task-list') + '?description__regex=^(Buy|Call)&completed=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(task1.id, result_ids)
        self.assertIn(task3.id, result_ids)

    def test_filter_by_created_after(self):
        """Test filtering tasks by creation time after a specific date."""
        base = timezone.now()

        yesterday = base - timedelta(days=1)
        two_days_ago = base - timedelta(days=2)
        three_days_ago = base - timedelta(days=3)

        TaskFactory(
            description="Recent task",
            user=self.normal_user,
            creation_time=yesterday
        )
        TaskFactory(
            description="Older task",
            user=self.normal_user,
            creation_time=two_days_ago
        )
        TaskFactory(
            description="Oldest task",
            user=self.normal_user,
            creation_time=three_days_ago
        )

        self.api_client.force_authenticate(user=self.normal_user)

        filter_date = (base - timedelta(days=2)).date().isoformat()
        response = self.api_client.get(reverse('task-list') + f"?created_after={filter_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        descriptions = [task["description"] for task in response.data["results"]]
        self.assertIn("Recent task", descriptions)
        self.assertIn("Older task", descriptions)
        self.assertNotIn("Oldest task", descriptions)

    def test_filter_by_created_before(self):
        """Test filtering tasks by creation time before a specific date."""
        base = timezone.now()

        yesterday = base - timedelta(days=1)
        two_days_ago = base - timedelta(days=2)
        three_days_ago = base - timedelta(days=3)

        TaskFactory(
            description="Recent task",
            user=self.normal_user,
            creation_time=yesterday
        )
        TaskFactory(
            description="Older task",
            user=self.normal_user,
            creation_time=two_days_ago
        )
        TaskFactory(
            description="Oldest task",
            user=self.normal_user,
            creation_time=three_days_ago
        )
        self.api_client.force_authenticate(user=self.normal_user)

        filter_date = (base - timedelta(days=2)).date().isoformat()
        response = self.api_client.get(reverse('task-list') + f"?created_before={filter_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        descriptions = [task["description"] for task in response.data["results"]]
        self.assertNotIn("Recent task", descriptions)
        self.assertIn("Older task", descriptions)
        self.assertIn("Oldest task", descriptions)

    def test_filter_by_created_on(self):
        """Test filtering tasks created on a specific date."""
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        TaskFactory(
            description="Today task 1",
            user=self.normal_user,
            creation_time=today
        )
        TaskFactory(
            description="Today task 2",
            user=self.normal_user,
            creation_time=today - timedelta(hours=2)
        )
        TaskFactory(
            description="Yesterday task",
            user=self.normal_user,
            creation_time=yesterday
        )
        TaskFactory(
            description="Two days ago task",
            user=self.normal_user,
            creation_time=two_days_ago
        )

        self.api_client.force_authenticate(user=self.normal_user)

        filter_date = today.date().isoformat()
        response = self.api_client.get(reverse('task-list') + f"?created_on={filter_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2, response.data)
        descriptions = [task["description"] for task in response.data["results"]]
        self.assertIn("Today task 1", descriptions)
        self.assertIn("Today task 2", descriptions)
        self.assertNotIn("Yesterday task", descriptions)
        self.assertNotIn("Two days ago task", descriptions)

    def test_combined_date_filters(self):
        """Test using multiple date filters together."""
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        three_days_ago = today - timedelta(days=3)
        four_days_ago = today - timedelta(days=4)

        TaskFactory(
            description="Today task",
            user=self.normal_user,
            creation_time=today
        )
        TaskFactory(
            description="Yesterday task",
            user=self.normal_user,
            creation_time=yesterday
        )
        TaskFactory(
            description="Two days ago task",
            user=self.normal_user,
            creation_time=two_days_ago
        )
        TaskFactory(
            description="Three days ago task",
            user=self.normal_user,
            creation_time=three_days_ago
        )
        TaskFactory(
            description="Four days ago task",
            user=self.normal_user,
            creation_time=four_days_ago
        )
        self.api_client.force_authenticate(user=self.normal_user)

        after_date = (today - timedelta(days=3)).date().isoformat()
        before_date = (today - timedelta(days=1)).date().isoformat()
        response = self.api_client.get(reverse('task-list') + f"?created_after={after_date}&created_before={before_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        descriptions = [task["description"] for task in response.data["results"]]
        self.assertNotIn("Today task", descriptions)
        self.assertIn("Yesterday task", descriptions)
        self.assertIn("Two days ago task", descriptions)
        self.assertIn("Three days ago task", descriptions)
        self.assertNotIn("Four days ago task", descriptions)

    def test_combined_date_and_description_filters(self):
        """Test combining date filters with description filters."""
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        TaskFactory(
            description="Work meeting today",
            user=self.normal_user,
            creation_time=today
        )
        TaskFactory(
            description="Work presentation yesterday",
            user=self.normal_user,
            creation_time=yesterday
        )
        TaskFactory(
            description="Work report two days ago",
            user=self.normal_user,
            creation_time=two_days_ago
        )
        TaskFactory(
            description="Personal task today",
            user=self.normal_user,
            creation_time=today
        )
        TaskFactory(
            description="Personal call yesterday",
            user=self.normal_user,
            creation_time=yesterday
        )
        self.api_client.force_authenticate(user=self.normal_user)

        after_date = (today - timedelta(days=1)).date().isoformat()
        response = self.api_client.get(reverse('task-list') + f"?description__contains=Work&created_after={after_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # Should return 2 tasks

        descriptions = [task["description"] for task in response.data["results"]]
        self.assertIn("Work meeting today", descriptions)
        self.assertIn("Work presentation yesterday", descriptions)
        self.assertNotIn("Work report two days ago", descriptions)
        self.assertNotIn("Personal task today", descriptions)
        self.assertNotIn("Personal call yesterday", descriptions)