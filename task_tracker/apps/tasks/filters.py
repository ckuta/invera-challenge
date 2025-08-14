import logging
from datetime import datetime, time
from typing import Tuple

from django.db.models import QuerySet
from django.utils import timezone

from django_filters import rest_framework
from task_tracker.apps.tasks.models import Task

logger = logging.getLogger(__name__)


class DescriptionFilter(rest_framework.FilterSet):
    """FilterSet for filtering tasks based on their description and completion status."""

    description = rest_framework.CharFilter(
        field_name='description',
        lookup_expr='iexact',
        help_text="Filter tasks by an exact (case-insensitive) match for the description."
    )
    description__contains = rest_framework.CharFilter(
        field_name='description',
        lookup_expr='icontains',
        help_text="Filter tasks where the description contains the specified string (case-insensitive)."
    )
    description__startswith = rest_framework.CharFilter(
        field_name='description',
        lookup_expr='istartswith',
        help_text="Filter tasks where the description starts with the specified string (case-insensitive)."
    )
    description__regex = rest_framework.CharFilter(
        field_name='description',
        lookup_expr='iregex',
        help_text="Filter tasks where the description matches the specified regex pattern (case-insensitive)."
    )

    class Meta:
        model = Task
        fields = ['description', 'completed']


class DateFilter(rest_framework.FilterSet):
    """FilterSet for filtering tasks by their creation time."""

    created_after = rest_framework.DateFilter(
        field_name='creation_time__date',
        lookup_expr='gte',
        help_text="Filter tasks created on or after the specified date (YYYY-MM-DD)."
    )
    created_before = rest_framework.DateFilter(
        field_name='creation_time__date',
        lookup_expr='lte',
        help_text="Filter tasks created on or before the specified date (YYYY-MM-DD)."
    )
    created_on = rest_framework.DateFilter(
        field_name='creation_time__date',
        method='filter_created_on',
        help_text="Filter tasks created on the exact specified date (YYYY-MM-DD). This includes the full day."
    )

    def filter_created_on(self, queryset, name, value) -> QuerySet:
        """Filter tasks created within the full day of the given date."""

        start_of_day, end_of_day = self._get_day_range(value)
        return queryset.filter(creation_time__range=(start_of_day, end_of_day))

    @staticmethod
    def _get_day_range(date_value) -> Tuple[datetime, datetime]:
        """Get the timezone-aware start and end of the day for the given date."""

        tz = timezone.get_current_timezone()
        start_of_day = timezone.make_aware(datetime.combine(date_value, time.min), tz)
        end_of_day = timezone.make_aware(datetime.combine(date_value, time.max), tz)
        return start_of_day, end_of_day

    class Meta:
        model = Task
        fields = ['created_after', 'created_before', 'created_on']


class TaskFilter(DescriptionFilter, DateFilter):
    class Meta:
        model = Task
        fields = [
            'description', 'description__contains', 'description__startswith', 'description__regex',
            'created_after', 'created_before', 'created_on', 'completed'
        ]

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        """Initialize the TaskFilter with the request to enable logging."""

        super().__init__(data, queryset, request=request, prefix=prefix)
        self.request = request

        if request and data:
            user_id = getattr(request.user, 'id', 'anonymous')
            applied_filters = [k for k in data.keys() if k in self.Meta.fields]

            if applied_filters:
                logger.info(f"User {user_id} applied filters: {', '.join(applied_filters)}")

    def filter_queryset(self, queryset):
        filtered_queryset = super().filter_queryset(queryset)

        if hasattr(self, 'request') and self.request and self.data:
            user_id = getattr(self.request.user, 'id', 'anonymous')
            original_count = queryset.count()
            filtered_count = filtered_queryset.count()

            logger.info(f"Filter results for user {user_id}: {filtered_count} tasks (from {original_count})")

        return filtered_queryset