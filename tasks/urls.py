from django.urls import path
from .views import *
from . import views
from .userview import *
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    # API Endpoints
    path('api/users/', UserViewSet.as_view(), name='user-list'),
    path('api/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('api/groups/', GroupListView.as_view(), name='group-list'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/tasks/', TaskListView.as_view(), name='task-list'),
    path('api/tasks/<int:pk>/', TaskUpdateView.as_view(), name='task-update'),
    path('api/tasks/<int:pk>/report/', TaskReportView.as_view(), name='task-report'),

    # User View
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('tasks/', UserTaskListView.as_view(), name='user_task_list'),
    path('tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task_update'),


    # Admin Panel URLs
    path('adminpanel/', views.admin_dashboard, name='admin_dashboard'),
    path('adminpanel/groups/', views.admin_group_list, name='admin_group_list'),
    path('adminpanel/groups/create/', views.admin_group_create, name='admin_group_create'),
    path('adminpanel/groups/<int:group_id>/delete/', views.admin_group_delete, name='admin_group_delete'),
    path('adminpanel/users/', views.admin_user_list, name='admin_user_list'),
    path('adminpanel/users/create/', views.admin_create_user, name='admin_create_user'),
    path('adminpanel/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('adminpanel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('adminpanel/tasks/', views.admin_task_list, name='admin_task_list'),
    path('adminpanel/tasks/assign/', views.admin_assign_task, name='admin_assign_task'),
]