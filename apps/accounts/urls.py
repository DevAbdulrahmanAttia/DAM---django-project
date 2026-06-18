from django.urls import path

from .views import (
    AccountsHealthCheckView,
    AdminDashboardStatsView,
    AdminUserDetailView,
    AdminUserListView,
    ProfileView,
)

app_name = 'accounts'

urlpatterns = [
    path('health/', AccountsHealthCheckView.as_view(), name='health'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('admin/stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
]
