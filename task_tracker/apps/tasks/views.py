import logging
from django.db.models import QuerySet
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from task_tracker.apps.tasks.filters import TaskFilter
from task_tracker.permissions import IsOwner
from task_tracker.apps.tasks.models import Task
from task_tracker.apps.tasks.serializers import ListTasksSerializer, TaskSerializer

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

logger = logging.getLogger(__name__)


@extend_schema(
    summary="List tasks for the authenticated user",
    description=(
            "Retrieve a list of tasks associated with the authenticated user.\n\n"
            "**Available Filters:**\n"
            "- `description`: Exact case-insensitive match.\n"
            "- `description__contains`: Case-insensitive partial match.\n"
            "- `description__startswith`: Case-insensitive prefix match.\n"
            "- `description__regex`: Match against a regex.\n"
            "- `completed`: Boolean filter to retrieve completed or incomplete tasks.\n"
            "- `created_after`: Tasks created on or after the specified date (`YYYY-MM-DD`).\n"
            "- `created_before`: Tasks created on or before the specified date (`YYYY-MM-DD`).\n"
            "- `created_on`: Tasks created on the exact specified date (`YYYY-MM-DD`).\n\n"
            "**Ordering Options:**\n"
            "- `creation_time`: Order by the creation time of the tasks.\n"
            "- `updated_at`: Order by the last update time of the tasks.\n"
            "- Default ordering: By `completed` status, then by descending `creation_time` and `updated_at`."
    ),
    parameters=[
        OpenApiParameter(name="description", type=str, location=OpenApiParameter.QUERY, description="Case-insensitive exact match for task descriptions."),
        OpenApiParameter(name="completed", type=bool, location=OpenApiParameter.QUERY, description="Boolean filter to retrieve completed (`true`) or incomplete (`false`) tasks."),
        OpenApiParameter(name="created_after", type=str, location=OpenApiParameter.QUERY, description="Filter tasks created on or after the specified date (`YYYY-MM-DD`)."),
        OpenApiParameter(name="created_before", type=str, location=OpenApiParameter.QUERY, description="Filter tasks created on or before the specified date (`YYYY-MM-DD`)."),
        OpenApiParameter(name="ordering", type=str, location=OpenApiParameter.QUERY, description="Specify the ordering of results (e.g., `creation_time`, `updated_at`)."),
    ],
    responses={
        200: OpenApiResponse(
            response=ListTasksSerializer(many=True),
            examples=[
                OpenApiExample(
                    name="Successful",
                    summary="Successful Example",
                    value=[
                        {"id": 1, "description": "Sample Task 1", "completed": False, "creation_time": "2025-08-10T10:00:00Z"},
                        {"id": 2, "description": "Sample Task 2", "completed": True, "creation_time": "2025-08-11T11:00:00Z"},
                    ]
                )
            ]
        ),
        401: OpenApiResponse(description="Authentication credentials were not provided.", examples=[OpenApiExample("Unauthorized Access", {"detail": "Authentication credentials were not provided."})]),
        400: OpenApiResponse(description="Invalid Query Parameters.", examples=[OpenApiExample("Bad Request", {"detail": "Invalid query parameters.", "errors": {"completed": "Invalid boolean value."}})]),
    }
)
class TaskListView(generics.ListAPIView):
    """List all tasks for the authenticated user."""
    serializer_class = ListTasksSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TaskFilter
    ordering_fields = ["creation_time", "updated_at"]
    ordering = ["completed", "-creation_time", "-updated_at"]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user = request.user
        if request.query_params:
            filters = ', '.join([f"{k}={v}" for k, v in request.query_params.items()])
            logger.info(f"User {user.username} (ID: {user.id}) listed tasks with filters: {filters}")
        else:
            logger.info(f"User {user.username} (ID: {user.id}) listed all their tasks")

        return super().list(request, *args, **kwargs)


@extend_schema(
    summary="Create a new task for the authenticated user",
    description="Create a new task and assign it to the authenticated user.",
    request=TaskSerializer,
    responses={
        201: TaskSerializer,
        400: OpenApiResponse(description="Validation Error", examples=[OpenApiExample("Invalid Data", {"description": ["This field is required."]})]),
        401: OpenApiResponse(description="Unauthorized", examples=[OpenApiExample("Unauthorized User", {"detail": "Authentication credentials were not provided."})]),
    }
)
class TaskCreateView(generics.ListCreateAPIView):
    """Create a new task for the authenticated user."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["post"]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        task = serializer.save(user=user)
        logger.info(f"User {user.username} (ID: {user.id}) created task with ID: {task.id}, description: '{task.description}'")


@extend_schema(
    summary="Retrieve a task by its ID",
    description="Retrieve the details of a specific task owned by the authenticated user.",
    responses={
        200: TaskSerializer,
        401: OpenApiResponse(description="Unauthorized", examples=[OpenApiExample("Unauthorized User", {"detail": "Authentication credentials were not provided."})]),
        404: OpenApiResponse(description="Not Found", examples=[OpenApiExample("Task Not Found", {"detail": "Not found."})]),
    }
)
class TaskDetailView(generics.RetrieveAPIView):
    """Retrieve the details of a specific task by ID."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        task_id = kwargs.get('pk')
        response = super().retrieve(request, *args, **kwargs)

        # Log only if task is found (to avoid logging 404 errors)
        if response.status_code == 200:
            logger.info(f"User {user.username} (ID: {user.id}) retrieved task with ID: {task_id}")

        return response


@extend_schema(
    summary="Update the description of a specific task",
    description="Update the `description` field of a task by its unique ID.",
    request=TaskSerializer,
    responses={
        200: TaskSerializer,
        400: OpenApiResponse(description="Validation Error", examples=[OpenApiExample("Invalid Data", {"description": ["This field may not be blank."]})]),
        401: OpenApiResponse(description="Unauthorized", examples=[OpenApiExample("Unauthorized User", {"detail": "Authentication credentials were not provided."})]),
        404: OpenApiResponse(description="Not Found", examples=[OpenApiExample("Task Not Found", {"detail": "Not found."})]),
    }
)
class TaskUpdateDescriptionView(generics.UpdateAPIView):
    """Update the description of a specific task by ID."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["patch"]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        user = request.user
        task_id = kwargs.get('pk')

        task = self.get_object()
        old_description = task.description

        response = super().update(request, *args, **kwargs)

        if 'description' in request.data:
            new_description = request.data['description']
            logger.info(f"User {user.username} (ID: {user.id}) updated task ID: {task_id} description from '{old_description}' to '{new_description}'")

        return response


@extend_schema(
    summary="Toggle a task's completion status",
    description="Toggle the `completed` status of a task by its unique ID.",
    responses={
        200: TaskSerializer,
        401: OpenApiResponse(description="Unauthorized", examples=[OpenApiExample("Unauthorized User", {"detail": "Authentication credentials were not provided."})]),
        404: OpenApiResponse(description="Not Found", examples=[OpenApiExample("Task Not Found", {"detail": "Not found."})]),
    }
)
class TaskToggleCompletionView(generics.UpdateAPIView):
    """Toggle the `completed` status of a task."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["patch"]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        task_id = kwargs.get('pk')

        old_status = "completed" if task.completed else "incomplete"

        task.toggle_completion()

        new_status = "completed" if task.completed else "incomplete"
        logger.info(f"User {user.username} (ID: {user.id}) toggled task ID: {task_id} status from {old_status} to {new_status}")

        serializer = self.get_serializer(task)
        return Response(serializer.data)


@extend_schema(
    summary="Delete a task by its ID",
    description="Delete a specific task permanently using its ID.",
    responses={
        204: OpenApiResponse(description="Task deleted successfully."),
        401: OpenApiResponse(description="Unauthorized", examples=[OpenApiExample("Unauthorized User", {"detail": "Authentication credentials were not provided."})]),
        404: OpenApiResponse(description="Not Found", examples=[OpenApiExample("Task Not Found", {"detail": "Not found."})]),
    }
)
class TaskDeleteView(generics.DestroyAPIView):
    """Delete a specific task by ID."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self) -> QuerySet[Task]:
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        task_id = kwargs.get('pk')

        task = self.get_object()
        task_description = task.description

        logger.info(f"User {user.username} (ID: {user.id}) deleted task ID: {task_id}, description: '{task_description}'")

        return super().destroy(request, *args, **kwargs)