import secrets
import string
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username_slug = models.SlugField(unique=True, max_length=160)
    display_name = models.CharField(max_length=60)
    bio = models.TextField(blank=True)
    city_default = models.CharField(max_length=80, blank=True)
    city_slug = models.SlugField(max_length=90, blank=True)
    likes_tags = models.JSONField(default=list, blank=True)
    fears_tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.username_slug:
            self.username_slug = slugify(self.user.username)
        if not self.display_name:
            self.display_name = self.user.get_full_name() or self.user.username
        if self.city_default:
            self.city_slug = slugify(self.city_default)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


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


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, display_name=instance.username)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
