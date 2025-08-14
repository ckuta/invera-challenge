import logging
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse
from django.contrib.auth.models import User
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from task_tracker.apps.users.filters import UserFilter

from .serializers import UserCreateSerializer, UserUpdateSerializer, UserSerializer
from task_tracker.permissions import IsOwnerOrStaff

logger = logging.getLogger(__name__)


@extend_schema_view(
    create=extend_schema(
        summary="Register a new user",
        description=(
                "This endpoint allows public registration of a new user account. "
                "No authentication is required to access this endpoint."
        ),
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                description="Invalid input data",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        summary="Invalid data example",
                        value={"username": ["This field is required."]}
                    )
                ]
            )
        }
    )
)
class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Endpoint for registering new user accounts."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        instance = serializer.save()
        logger.info(f"User created: {instance.username} (ID: {instance.id})")
        return instance


@extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve a user profile",
        description=(
                "Retrieve the profile details of a specific user by their ID.\n\n"
                "**Access rules:**\n"
                "- Authenticated users can only access their own profile.\n"
                "- Staff and superusers can access any profile."
        ),
        responses={
            200: UserSerializer,
            403: OpenApiResponse(
                description="Forbidden",
                examples=[
                    OpenApiExample(
                        "Forbidden Access",
                        summary="User trying to access another's profile",
                        value={"detail": "You do not have permission to access this profile."}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Profile not found",
                examples=[
                    OpenApiExample(
                        "Not Found",
                        value={"detail": "Not found."}
                    )
                ]
            )
        }
    ),
    update=extend_schema(
        summary="Update a user profile",
        description=(
                "Perform a complete update of a specific user profile.\n\n"
                "**Access rules:**\n"
                "- Users can only update their own profile.\n"
                "- Staff and superusers can update any profile."
        ),
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                description="Invalid input data",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={"email": ["Enter a valid email address."]}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        "Forbidden Access",
                        value={"detail": "You do not have permission to update this profile."}
                    )
                ]
            )
        }
    ),
    partial_update=extend_schema(
        summary="Partially update a user profile",
        description=(
                "Update specific fields of a user profile without replacing the whole object.\n\n"
                "**Access rules:**\n"
                "- Users can partially update their own profile.\n"
                "- Staff and superusers can partially update any profile."
        ),
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                description="Invalid input data",
                examples=[
                    OpenApiExample(
                        "Validation Error",
                        value={"email": ["Enter a valid email address."]}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        "Forbidden Access",
                        value={"detail": "You do not have permission to update this profile."}
                    )
                ]
            )
        }
    ),
    destroy=extend_schema(
        summary="Delete a user profile",
        description=(
                "Delete a user profile by its ID.\n\n"
                "**Access rules:**\n"
                "- Users can delete their own profile.\n"
                "- Staff and superusers can delete any profile."
        ),
        responses={
            204: OpenApiResponse(description="Successfully deleted."),
            403: OpenApiResponse(
                description="Permission denied",
                examples=[
                    OpenApiExample(
                        "Forbidden Access",
                        value={"detail": "You do not have permission to delete this profile."}
                    )
                ]
            ),
            404: OpenApiResponse(description="Profile not found.")
        }
    )
)
class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """ViewSet to retrieve, update, or delete a user's profile."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        return super().get_queryset()

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        requested_user_id = kwargs.get('pk')

        if not user.is_staff and str(user.id) != requested_user_id:
            logger.warning(f"User {user.username} (ID: {user.id}) attempted to access profile of user ID: {requested_user_id}")
            raise PermissionDenied("You do not have permission to access this profile.")

        logger.info(f"User {user.username} (ID: {user.id}) retrieved profile with ID: {requested_user_id}")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        user = request.user
        updated_user_id = kwargs.get('pk')
        logger.info(f"User {user.username} (ID: {user.id}) performed full update on profile with ID: {updated_user_id}")
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        user = request.user
        updated_user_id = kwargs.get('pk')
        updated_fields = ", ".join(request.data.keys())
        logger.info(f"User {user.username} (ID: {user.id}) partially updated profile with ID: {updated_user_id}. Fields: {updated_fields}")
        return response

    def destroy(self, request, *args, **kwargs):
        user = request.user
        user_to_delete_id = kwargs.get('pk')
        user_to_delete = self.get_object()
        logger.info(f"User {user.username} (ID: {user.id}) deleted profile: {user_to_delete.username} (ID: {user_to_delete_id})")
        return super().destroy(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(
        summary="List users with filtering options",
        description=(
                "Retrieve a list of all registered users with optional filters.\n\n"
                "**Access rules:**\n"
                "- Staff and superusers can view all registered users.\n"
                "- Regular users can only see their own profile."
        ),
        parameters=[
            OpenApiParameter(
                name="username",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter users by username (case insensitive)."
            ),
            OpenApiParameter(
                name="email",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter users by email address (case insensitive)."
            )
        ],
        responses={
            200: OpenApiResponse(
                response=UserSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Filtered List",
                        value=[
                            {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com",
                                "first_name": "John",
                                "last_name": "Doe"
                            }
                        ]
                    )
                ]
            )
        }
    )
)
class UserListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ViewSet to list registered users with filtering options."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        user = self.request.user

        if user.is_staff or user.is_superuser:
            logger.info(f"Staff user {user.username} (ID: {user.id}) accessed the list of all users")
            return User.objects.all()

        logger.info(f"Regular user {user.username} (ID: {user.id}) accessed their own profile")
        return User.objects.filter(id=user.id)

    def list(self, request, *args, **kwargs):
        # Log query parameters if they exist
        if request.query_params:
            filters = ', '.join([f"{k}={v}" for k, v in request.query_params.items()])
            logger.info(f"User {request.user.username} (ID: {request.user.id}) filtered users with: {filters}")

        return super().list(request, *args, **kwargs)