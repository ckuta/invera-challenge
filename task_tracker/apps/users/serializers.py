from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.models import User


class PasswordSerializer(serializers.Serializer):
    """Serializer for handling password validation."""
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="The user's password. Must meet the system password validation rules."
    )


class UserCreateSerializer(PasswordSerializer, serializers.ModelSerializer):
    """
    Serializer for user creation.
    Extends the base model serializer to include password and activation fields.
    """
    is_active = serializers.BooleanField(
        default=True,
        help_text="Indicates whether the user account is active. Defaults to 'True'."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'is_active']
        extra_kwargs = {
            'username': {
                'help_text': "Unique username for the user. This field is required."
            },
            'email': {
                'help_text': "The user's email address. Must be a valid email format."
            },
            'first_name': {
                'help_text': "The user's first name."
            },
            'last_name': {
                'help_text': "The user's last name."
            },
            'password': {
                'write_only': True,
                'help_text': "The user's password. Must meet the system's password validation rules."
            },
        }


class UserUpdateSerializer(PasswordSerializer, serializers.ModelSerializer):
    """
    Serializer for updating user details.
    Supports updates to email, first name, last name, and password.
    """
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'email': {
                'help_text': "The updated email address of the user."
            },
            'first_name': {
                'help_text': "The updated first name of the user."
            },
            'last_name': {
                'help_text': "The updated last name of the user."
            },
            'password': {
                'write_only': True,
                'help_text': "The updated password for the user. Must meet the system's password validation rules."
            },
        }

    def update(self, instance, validated_data):
        """Custom update method for handling password updates alongside other fields."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    """
    Simple serializer for returning user details.
    Provides public information about the user (e.g., id, username, email, first name, last name).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {
                'help_text': "Unique username of the user."
            },
            'email': {
                'help_text': "The user's email address."
            },
            'first_name': {
                'help_text': "The user's first name."
            },
            'last_name': {
                'help_text': "The user's last name."
            },
        }