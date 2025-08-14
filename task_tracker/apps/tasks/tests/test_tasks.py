from task_tracker.test import TestCase
from task_tracker.apps.tasks.factories import TaskFactory, UserFactory
from task_tracker.apps.tasks.models import Task


class TestTaskModel(TestCase):
    def test_create_task(self):
        """Test creating tasks with different completion states."""
        incomplete_task = TaskFactory(
            user=self.user,
            description="Incomplete task",
            completed=False,
        )

        completed_task = TaskFactory(
            user=self.user,
            description="Completed task",
            completed=True,
        )

        tasks = Task.objects.filter(user=self.user).order_by('id')
        self.assertEqual(tasks.count(), 2)

        self.assertEqual(tasks[0], incomplete_task)
        self.assertEqual(tasks[0].description, "Incomplete task")
        self.assertFalse(tasks[0].completed)

        self.assertEqual(tasks[1], completed_task)
        self.assertEqual(tasks[1].description, "Completed task")
        self.assertTrue(tasks[1].completed)

    def test_task_user_association(self):
        """Test task-user associations and filtering."""
        other_user = UserFactory()

        self_task = TaskFactory(user=self.user)
        other_task = TaskFactory(user=other_user)

        self.assertIn(self_task, Task.objects.filter(user=self.user))
        self.assertNotIn(other_task, Task.objects.filter(user=self.user))
        self.assertIn(other_task, Task.objects.filter(user=other_user))
        self.assertNotIn(self_task, Task.objects.filter(user=other_user))

    def test_task_str_representation(self):
        """Test string representation with various description lengths."""
        short_desc = "Short description"
        short_task = TaskFactory(user=self.user, description=short_desc)
        self.assertEqual(str(short_task), short_desc)
        self.assertFalse('...' in str(short_task))

        exact_desc = "X" * 50
        exact_task = TaskFactory(user=self.user, description=exact_desc)
        self.assertEqual(str(exact_task), exact_desc)
        self.assertFalse('...' in str(exact_task))

        long_desc = "This description is definitely longer than fifty characters and should be trimmed"
        long_task = TaskFactory(user=self.user, description=long_desc)

        str_repr = str(long_task)
        self.assertEqual(len(str_repr), 53)
        self.assertTrue(str_repr.endswith('...'))
        self.assertEqual(str_repr, long_desc[:50] + '...')

        # Original description should be intact
        self.assertEqual(long_task.description, long_desc)

    def test_task_validation(self):
        """Test task validation rules."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TaskFactory(user=None)

    def test_task_updates(self):
        """Test updating task attributes."""
        task = TaskFactory(
            user=self.user,
            description="Original description",
            completed=False
        )

        task.description = "Updated description"
        task.completed = True
        task.save()

        refreshed_task = Task.objects.get(id=task.id)
        self.assertEqual(refreshed_task.description, "Updated description")
        self.assertTrue(refreshed_task.completed)

        self.assertNotEqual(refreshed_task.updated_at, refreshed_task.creation_time)

    def test_task_ordering(self):
        """Test default task ordering is by creation time (newest first)."""
        first_task = TaskFactory(user=self.user, description="First created")
        second_task = TaskFactory(user=self.user, description="Second created")

        tasks = Task.objects.filter(user=self.user)
        self.assertEqual(list(tasks), [second_task, first_task])