from django.http import HttpResponseForbidden, HttpResponseRedirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User, Group
from .models import Task
from .serializers import TaskSerializer, UserSerializer, GroupSerializer
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from .forms import GroupForm


def is_superadmin(user):
    return user.is_superuser

def is_admin(user):
    return user.is_superuser or user.groups.filter(name=settings.ADMIN_GROUP_NAME).exists()


class UserViewSet(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]  # Only admin can list/create users


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class GroupListView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class TaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(assigned_to=user)


class TaskUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # check if the user is assigned to the task.
        if instance.assigned_to != request.user:
            return Response({"message": "You are not allowed to update this task."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_update(serializer)
        return Response(serializer.data)


class TaskReportView(generics.RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the task is completed
        if instance.status != 'Completed':
            return Response({"message": "Report is only available for completed tasks."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is an admin or superadmin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({"message": "You are not authorized to view this report."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance)
        return Response({
            "completion_report": serializer.data.get('completion_report'),
            "worked_hours": serializer.data.get('worked_hours'),
        })


@user_passes_test(is_admin)
def admin_task_list(request):
    user_group = request.user.groups.first()

    if request.user.is_superuser:
        tasks = Task.objects.all()
    else:
        assigned_users = User.objects.filter(groups=user_group)
        tasks = Task.objects.filter(assigned_to__in=assigned_users)

    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'current_status': status_filter
    }
    return render(request, 'admin_task_list.html', context)


@user_passes_test(is_superadmin)
def admin_user_list(request):
    users = User.objects.all().order_by('id')
    context = {'users': users}
    return render(request, 'admin_user_list.html', context)


@user_passes_test(is_superadmin)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    groups = Group.objects.all()

    if request.method == 'POST':
        # Handle user update
        username = request.POST.get('username')
        email = request.POST.get('email')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        group_id = request.POST.get('group')

        user.username = username
        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()

        if group_id:
            group = Group.objects.get(id=group_id)
            user.groups.set([group])
        else:
            user.groups.clear()

        messages.success(request, 'User updated successfully')
        return HttpResponseRedirect(reverse('admin_user_detail', args=[user_id]))

    context = {
        'user': user,
        'groups': groups
    }
    return render(request, 'admin_user_detail.html', context)


@user_passes_test(is_superadmin)
def admin_create_user(request):
    groups = Group.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        group_id = request.POST.get('group')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser
            )

            if group_id:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)

            messages.success(request, 'User created successfully')
            return HttpResponseRedirect(reverse('admin_user_list'))
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')

    context = {'groups': groups}
    return render(request, 'admin_create_user.html', context)


@user_passes_test(is_admin)
def admin_assign_task(request):
    user_group = request.user.groups.first()

    if request.user.is_superuser:
        users = User.objects.all()
    else:
        users = User.objects.filter(groups=user_group)

    if request.method == 'POST':
        task_title = request.POST.get('task_title')
        task_description = request.POST.get('task_description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date_str = request.POST.get('due_date')

        assigned_to = get_object_or_404(User, id=assigned_to_id)
        due_date = timezone.datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')

        Task.objects.create(
            title=task_title,
            description=task_description,
            assigned_to=assigned_to,
            due_date=due_date,
            created_by=request.user
        )
        messages.success(request, 'Task assigned successfully')
        return redirect('admin_task_list')

    context = {'users': users}
    return render(request, 'admin_assign_task.html', context)


@user_passes_test(is_superadmin)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully')
        return HttpResponseRedirect(reverse('admin_user_list'))

    return render(request, 'admin_confirm_delete.html', {'user': user})


@user_passes_test(is_superadmin, login_url='/admin/login/')
def admin_dashboard(request):
    context = {
        'user_count': User.objects.count(),
        'group_count': Group.objects.count(),
        'task_count': Task.objects.count()
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(is_superadmin)
def admin_group_list(request):
    groups = Group.objects.all()
    return render(request, 'admin_group_list.html', {'groups': groups})

@user_passes_test(is_superadmin)
def admin_group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group created successfully')
            return redirect('admin_group_list')
    else:
        form = GroupForm()
    return render(request, 'admin_group_create.html', {'form': form})

@user_passes_test(is_superadmin)
def admin_group_delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group deleted successfully')
        return redirect('admin_group_list')
    return render(request, 'admin_confirm_delete.html', {
        'object': group,
        'object_type': 'group'
    })