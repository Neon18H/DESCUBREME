import secrets
import string
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class UserProfile(models.Model):
    VIBE_CHOICES = [
        ('chill', 'Chill'),
        ('foodie', 'Foodie'),
        ('cultural', 'Cultural'),
        ('adventure', 'Adventure'),
        ('rumba_suave', 'Rumba suave'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=60)
    username_slug = models.SlugField(unique=True, max_length=160)
    about = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    country = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    city_default = models.CharField(max_length=80, blank=True)
    city_slug = models.SlugField(max_length=90, blank=True)
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=60, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)

    likes_tags = models.JSONField(default=list, blank=True)
    hobbies_tags = models.JSONField(default=list, blank=True)
    avoid_tags = models.JSONField(default=list, blank=True)
    budget_min_cop = models.IntegerField(null=True, blank=True)
    budget_max_cop = models.IntegerField(null=True, blank=True)
    max_distance_km = models.IntegerField(default=8)
    preferred_vibes = models.JSONField(default=list, blank=True)

    is_private = models.BooleanField(default=False)
    show_city = models.BooleanField(default=True)
    show_tags = models.BooleanField(default=True)
    allow_friend_requests = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.budget_min_cop and self.budget_max_cop and self.budget_min_cop > self.budget_max_cop:
            raise ValidationError('El presupuesto mínimo no puede ser mayor que el máximo.')

    def save(self, *args, **kwargs):
        if not self.username_slug:
            self.username_slug = slugify(self.user.username)
        if not self.display_name:
            self.display_name = self.user.get_full_name() or self.user.username
        city_reference = self.city or self.city_default
        if city_reference:
            self.city_slug = slugify(city_reference)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class FriendRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ACCEPTED = 'accepted', 'Aceptada'
        REJECTED = 'rejected', 'Rechazada'
        CANCELED = 'canceled', 'Cancelada'

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['from_user', 'to_user'],
                condition=Q(status='pending'),
                name='uniq_pending_request',
            ),
        ]

    def clean(self):
        if self.from_user_id == self.to_user_id:
            raise ValidationError('No puedes enviarte una solicitud a ti mismo.')


class Friendship(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_friend_pair'),
        ]

    def save(self, *args, **kwargs):
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
        super().save(*args, **kwargs)

    @classmethod
    def are_friends(cls, user_a, user_b):
        if not user_a or not user_b or user_a == user_b:
            return False
        user1, user2 = sorted([user_a.id, user_b.id])
        return cls.objects.filter(user1_id=user1, user2_id=user2).exists()


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plans')
    title = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    city_slug = models.SlugField(max_length=90)
    mood = models.CharField(max_length=40, blank=True)
    group = models.CharField(max_length=40, blank=True)
    budget_cop = models.IntegerField(null=True, blank=True)
    prompt_text = models.TextField()
    plan_json = models.JSONField(default=dict)
    is_public = models.BooleanField(default=False)
    share_code = models.CharField(max_length=12, unique=True, blank=True)
    likes_count = models.IntegerField(default=0)
    saves_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.city_slug:
            self.city_slug = slugify(self.city)
        if not self.share_code:
            alphabet = string.ascii_letters + string.digits
            self.share_code = ''.join(secrets.choice(alphabet) for _ in range(12))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PlanItem(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='items')
    time_label = models.CharField(max_length=20)
    order = models.IntegerField(default=0)
    place_id = models.CharField(max_length=80)
    name = models.CharField(max_length=200)
    rating = models.FloatField(null=True, blank=True)
    user_ratings_total = models.IntegerField(null=True, blank=True)
    price_level = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    photo_reference = models.TextField(blank=True)
    photo_url = models.TextField(blank=True)
    maps_url = models.TextField(blank=True)

    class Meta:
        ordering = ['time_label', 'order']


class PlanLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_likes')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'plan'], name='unique_plan_like')]


class PlanSave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_saves')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'plan'], name='unique_plan_save')]
