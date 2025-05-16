from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )
    title = models.CharField(max_length=200, verbose_name="Task Title")
    description = models.TextField(verbose_name="Task Description")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name="Assigned To")
    due_date = models.DateTimeField(verbose_name="Due Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="Task Status")
    completion_report = models.TextField(blank=True, null=True, verbose_name="Completion Report")
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Worked Hours")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', verbose_name="Created By")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"