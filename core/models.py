import uuid

from django.contrib.auth.models import User
from django.db import models


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='plans')
    city = models.CharField(max_length=120)
    mood = models.CharField(max_length=40)
    start_time = models.TimeField()
    end_time = models.TimeField()
    budget_cop = models.PositiveIntegerField()
    group_size = models.PositiveSmallIntegerField()
    transport = models.CharField(max_length=40)
    interests = models.JSONField(default=list)
    raw_places = models.JSONField(default=dict)
    ai_plan_json = models.JSONField(default=dict)
    title = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)
    is_saved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class PlanStep(models.Model):
    BLOCK_CHOICES = [('tarde', 'Tarde'), ('noche', 'Noche')]

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='steps')
    block = models.CharField(max_length=10, choices=BLOCK_CHOICES)
    order = models.PositiveIntegerField()
    place_name = models.CharField(max_length=180)
    address = models.CharField(max_length=220, blank=True)
    rating = models.FloatField(null=True, blank=True)
    maps_url = models.URLField(blank=True, null=True)
    est_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    est_cost_cop = models.PositiveIntegerField(null=True, blank=True)
    why = models.TextField()
    description = models.TextField()

    class Meta:
        ordering = ['block', 'order']
