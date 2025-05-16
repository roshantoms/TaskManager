from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .serializers import TaskSerializer


class UserLoginView(View):
    def get(self, request):
        return render(request, 'user_login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('user_task_list')
        return render(request, 'user_login.html', {'error': 'Invalid credentials'})


class UserTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        return render(request, 'user_task_list.html', {'tasks': tasks})


class TaskUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        task = Task.objects.get(pk=pk, assigned_to=request.user)
        return render(request, 'task_update.html', {'task': task})

    def post(self, request, pk):
        task = Task.objects.get(pk=pk, assigned_to=request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            # Validate completion report requirements
            if request.data.get('status') == 'Completed':
                if not all([request.data.get('completion_report'), request.data.get('worked_hours')]):
                    return Response({
                        "error": "Completion report and worked hours are required when marking as completed"
                    }, status=400)

            serializer.save()
            return redirect('user_task_list')

        return Response(serializer.errors, status=400)