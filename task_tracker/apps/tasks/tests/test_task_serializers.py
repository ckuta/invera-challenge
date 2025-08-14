from task_tracker.test import TestCase
from task_tracker.apps.tasks.serializers import ListTasksSerializer, TaskSerializer
from task_tracker.apps.tasks.factories import UserFactory, TaskFactory


class TestTaskSerializers(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_list_tasks_serializer(self):
        """Test ListTasksSerializer handles description trimming correctly."""
        long_task = TaskFactory(
            user=self.user,
            description="This is a very long task description that exceeds 50 characters and should be trimmed."
        )

        short_task = TaskFactory(
            user=self.user,
            description="Short description"
        )

        long_serializer = ListTasksSerializer(long_task)
        short_serializer = ListTasksSerializer(short_task)

        self.assertEqual(set(long_serializer.data.keys()), {'id', 'description', 'completed', 'creation_time'})

        self.assertEqual(long_serializer.data['description'], str(long_task))
        self.assertTrue("..." in long_serializer.data['description'])

        self.assertEqual(short_serializer.data['description'], str(short_task))
        self.assertFalse("..." in short_serializer.data['description'])

    def test_task_serializer(self):
        """Test TaskSerializer handles full task details correctly."""
        task = TaskFactory(user=self.user, description="Test task description")
        serializer = TaskSerializer(task)

        self.assertEqual(
            set(serializer.data.keys()),
            {'id', 'description', 'completed', 'creation_time', 'updated_at'}
        )

        # Check that full description is preserved (not trimmed)
        self.assertEqual(serializer.data['description'], task.description)

        # Check other fields
        self.assertEqual(serializer.data['completed'], task.completed)
        serialized_creation_time = serializer.data['creation_time']
        self.assertIn(task.creation_time.strftime('%Y-%m-%dT%H:%M:%S'), serialized_creation_time)

    def test_task_serializer_read_only_fields(self):
        """Test TaskSerializer respects read-only fields."""
        task = TaskFactory(user=self.user)

        input_data = {
            'description': 'New description',
            'completed': True,  # Read-only
            'creation_time': '2023-01-01T00:00:00Z',  # Read-only
            'updated_at': '2023-01-01T00:00:00Z'  # Read-only
        }

        serializer = TaskSerializer(instance=task, data=input_data, partial=True)
        self.assertTrue(serializer.is_valid())

        self.assertEqual(set(serializer.validated_data.keys()), {'description'})

        updated_task = serializer.save()
        self.assertEqual(updated_task.description, 'New description')
        self.assertNotEqual(updated_task.completed, True)  # Shouldn't be changed
        self.assertNotEqual(updated_task.creation_time.isoformat(), '2023-01-01T00:00:00Z')

    def test_task_serializer_validation(self):
        """Test TaskSerializer validation rules."""
        serializer = TaskSerializer(data={'description': ''})
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

        serializer = TaskSerializer(data={'description': 'Valid task'})
        self.assertTrue(serializer.is_valid())

    def test_task_serializer_create(self):
        """Test TaskSerializer can create a task with user association."""
        serializer = TaskSerializer(data={'description': 'New task'})
        self.assertTrue(serializer.is_valid())

        task = serializer.save(user=self.user)

        self.assertEqual(task.description, 'New task')
        self.assertEqual(task.user, self.user)
        self.assertFalse(task.completed)  # Default is False