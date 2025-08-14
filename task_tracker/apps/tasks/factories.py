import factory
from django.utils import timezone
from task_tracker.apps.tasks.models import Task
from task_tracker.apps.users.factories import UserFactory


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Task instances for testing purposes."""

    class Meta:
        model = Task

    user = factory.SubFactory(UserFactory)
    description = factory.Faker('paragraph', nb_sentences=3)
    completed = False
    creation_time = factory.LazyFunction(timezone.now)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default _create method to handle auto_now fields."""
        creation_time = kwargs.pop('creation_time', None)
        updated_at = kwargs.pop('updated_at', None)

        obj = super()._create(model_class, *args, **kwargs)

        if creation_time is not None or updated_at is not None:
            updates = {}
            if creation_time is not None:
                updates['creation_time'] = creation_time

            if updated_at is not None:
                updates['updated_at'] = updated_at


            model_class.objects.filter(pk=obj.pk).update(**updates)
            obj.refresh_from_db()

        return obj


class CompletedTaskFactory(TaskFactory):
    """Factory for creating completed Task instances."""

    completed = True
