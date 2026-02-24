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


class FavoritePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_plans')
    prompt = models.TextField()
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=8, blank=True)
    mood = models.CharField(max_length=40)
    group = models.CharField(max_length=80, blank=True)
    budget_cop = models.PositiveIntegerField(default=0)
    source_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class FavoritePlace(models.Model):
    favorite_plan = models.ForeignKey(FavoritePlan, on_delete=models.CASCADE, related_name='places')
    window_label = models.CharField(max_length=50)
    window_start = models.CharField(max_length=10, blank=True)
    window_end = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=180)
    place_id = models.CharField(max_length=200)
    rating = models.FloatField(null=True, blank=True)
    user_ratings_total = models.PositiveIntegerField(null=True, blank=True)
    price_level = models.IntegerField(null=True, blank=True)
    estimated_cost_cop = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    photo_url = models.URLField(blank=True)
    maps_url = models.URLField(blank=True)
    raw_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['window_label', '-rating', 'name']
