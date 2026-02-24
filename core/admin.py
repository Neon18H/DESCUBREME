from django.contrib import admin

from core.models import FriendRequest, Friendship, Plan, PlanItem, PlanLike, PlanSave, UserProfile


class PlanItemInline(admin.TabularInline):
    model = PlanItem
    extra = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'is_public', 'likes_count', 'saves_count', 'created_at')
    search_fields = ('title', 'city', 'owner__username', 'share_code')
    list_filter = ('is_public', 'city_slug', 'created_at')
    inlines = [PlanItemInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'city', 'country', 'is_private', 'allow_friend_requests', 'updated_at')
    search_fields = ('user__username', 'display_name', 'city', 'country', 'city_default')


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    search_fields = ('user1__username', 'user2__username')


admin.site.register(PlanItem)
admin.site.register(PlanLike)
admin.site.register(PlanSave)
