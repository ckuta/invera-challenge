from rest_framework import serializers
from .models import Task


class ListTasksSerializer(serializers.ModelSerializer):
    """
    Serializer for listing tasks.

    This serializer provides a shortened version of the task's `description`
    (via the model's `__str__` method). Use it when only a brief summary of
    tasks is required, such as in listings.
    """
    description = serializers.SerializerMethodField(
        help_text="A shortened version of the task's description."
    )

    class Meta:
        model = Task
        fields = ['id', 'description', 'completed', 'creation_time']
        extra_kwargs = {
            'id': {
                'help_text': "The unique identifier of the task."
            },
            'completed': {
                'help_text': "Indicates whether the task is completed (True or False)."
            },
            'creation_time': {
                'help_text': "The timestamp when the task was created (read-only)."
            },
        }

    def get_description(self, instance: Task) -> str:
        """Returns a shortened version of the task's description by using the model's `__str__` method."""
        return str(instance)  # The __str__ method of the Task model


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for managing tasks.

    Use this serializer for creating, updating, and retrieving full details of a task.
    It includes fields for both metadata (such as creation time) and task content.
    """
    class Meta:
        model = Task
        fields = ['id', 'description', 'completed', 'creation_time', 'updated_at']
        read_only_fields = ['creation_time', 'updated_at', 'completed']
        extra_kwargs = {
            'id': {
                'help_text': "The unique identifier of the task."
            },
            'description': {
                'help_text': "A detailed description of the task."
            },
            'completed': {
                'help_text': "Indicates whether the task is completed. Defaults to False.",
                'read_only': True
            },
            'creation_time': {
                'help_text': "The timestamp when the task was created (read-only)."
            },
            'updated_at': {
                'help_text': "The timestamp when the task was last updated (read-only)."
            },
        }