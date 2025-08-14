from django.urls import path
from task_tracker.apps.tasks.views import (
    TaskListView,
    TaskCreateView,
    TaskDetailView,
    TaskUpdateDescriptionView,
    TaskToggleCompletionView,
    TaskDeleteView,
)

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('create/', TaskCreateView.as_view(), name='task-create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/update-description/', TaskUpdateDescriptionView.as_view(), name='task-update-description'),
    path('<int:pk>/toggle-complete/', TaskToggleCompletionView.as_view(), name='task-toggle-complete'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
]