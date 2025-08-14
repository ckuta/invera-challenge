from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    """
    Model representing a task in the system.

    Each task is owned by a user and can only be viewed by its owner.
    Tasks track creation time, completion status, and description.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='User who owns this task',
    )

    description = models.TextField(
        help_text='Description of the task',
        blank=False,
        null=False,
    )

    completed = models.BooleanField(
        default=False,
        help_text='Whether the task has been completed',
    )

    creation_time = models.DateTimeField(
        auto_now_add=True,
        help_text='When the task was created'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the task was last updated'
    )

    class Meta:
        ordering = ['-creation_time']  # Newest tasks first
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f"{(self.description[:50])}{'...' if len(self.description) > 50 else ''}"

    def toggle_completion(self):
        """Toggles the completion status of the task"""
        self.completed = not self.completed
        self.save()