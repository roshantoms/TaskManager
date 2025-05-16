from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Task


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser', 'groups']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        groups_data = validated_data.pop('groups', [])
        user = User.objects.create_user(**validated_data)
        for group_data in groups_data:
            group = Group.objects.get(id=group_data['id'])
            user.groups.add(group)
        return user


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_to', 'assigned_to_id',
            'due_date', 'status', 'completion_report', 'worked_hours',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'title', 'description', 'due_date']

    def validate(self, data):
        if data.get('status') == 'Completed':
            if data.get('completion_report') is None:
                raise serializers.ValidationError(
                    "Completion report is required when the task is completed."
                )
            if data.get('worked_hours') is None:
                raise serializers.ValidationError(
                    "Worked hours are required when the task is completed."
                )
        return data