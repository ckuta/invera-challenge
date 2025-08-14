from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import random
from task_tracker.apps.users.factories import UserFactory
from task_tracker.apps.tasks.factories import TaskFactory

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data using factory_boy'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with sample data...')

        common_password = 'password123'

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            admin = UserFactory(
                username='admin',
                email='admin@example.com',
                password=common_password,
                first_name='Admin',
                last_name='User',
                is_superuser=True,
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {admin.username}'))
        else:
            admin = User.objects.filter(is_superuser=True).first()
            self.stdout.write('Superuser already exists, skipping creation')

        staff_count = User.objects.filter(is_staff=True, is_superuser=False).count()
        if staff_count < 2:
            self.stdout.write('Creating staff users...')
            staff_to_create = 2 - staff_count
            staff_users = UserFactory.create_batch(
                size=staff_to_create,
                password=common_password,
                is_staff=True,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS(f'Created {len(staff_users)} staff users'))

        regular_count = User.objects.filter(is_staff=False, is_superuser=False).count()
        if regular_count < 10:
            self.stdout.write('Creating regular users...')
            users_to_create = 10 - regular_count
            regular_users = UserFactory.create_batch(
                size=users_to_create,
                password=common_password,
                is_staff=False,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS(f'Created {len(regular_users)} regular users'))

        all_users = list(User.objects.all())

        from task_tracker.apps.tasks.models import Task
        task_count = Task.objects.count()
        if task_count < 30:
            self.stdout.write('Creating tasks...')
            tasks_to_create = 30 - task_count

            task_descriptions = [
                "Revisar documentación del proyecto",
                "Actualizar dependencias del sistema",
                "Escribir pruebas unitarias",
                "Implementar nueva funcionalidad",
                "Corregir bugs reportados",
                "Optimizar consultas a la base de datos",
                "Refactorizar código legacy",
                "Revisar pull requests pendientes",
                "Configurar CI/CD pipeline",
                "Actualizar documentación de API"
            ]

            new_tasks = []
            for _ in range(tasks_to_create):
                user = random.choice(all_users)

                description = random.choice(task_descriptions) + f" para {user.username}"
                completed = random.choice([True, False])
                task = TaskFactory(
                    user=user,
                    description=description,
                    completed=completed
                )
                new_tasks.append(task)

            self.stdout.write(self.style.SUCCESS(f'Created {len(new_tasks)} tasks'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
        self.stdout.write(self.style.WARNING(f'All the users have the password: {common_password}'))
