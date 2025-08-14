import logging
import django_filters
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class UserFilter(django_filters.FilterSet):
    """FilterSet for filtering users by username or email."""

    username = django_filters.CharFilter(
        field_name='username',
        lookup_expr='icontains',
        help_text="Filter users by username (case insensitive)."
    )
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        help_text="Filter users by email address (case insensitive)."
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        """Initialize the UserFilter with the request to enable logging."""

        super().__init__(data, queryset, request=request, prefix=prefix)
        self.request = request

        if request and data:
            admin_user_id = getattr(request.user, 'id', 'anonymous')
            applied_filters = [k for k in data.keys() if k in self.Meta.fields]

            if applied_filters:
                logger.info(f"Admin user {admin_user_id} filtered users by: {', '.join(applied_filters)}")

    def filter_queryset(self, queryset):
        filtered_queryset = super().filter_queryset(queryset)

        if hasattr(self, 'request') and self.request and self.data:
            admin_user_id = getattr(self.request.user, 'id', 'anonymous')
            original_count = queryset.count()
            filtered_count = filtered_queryset.count()

            search_terms = []
            if 'username' in self.data:
                search_terms.append(f"username: '{self.data['username']}'")
            if 'email' in self.data:
                search_terms.append(f"email: '{self.data['email']}'")

            terms_str = " and ".join(search_terms) if search_terms else "no specific terms"

            logger.info(
                f"User search by admin {admin_user_id}: {filtered_count} users found "
                f"(from {original_count}) using {terms_str}"
            )

        return filtered_queryset