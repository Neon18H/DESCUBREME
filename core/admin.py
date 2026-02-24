from django.contrib import admin

from core.models import (
    Conversation,
    FriendRequest,
    Friendship,
    Message,
    Plan,
    PlanComment,
    PlanItem,
    PlanJoin,
    PlanLike,
    PlanSave,
    UserProfile,
)


class PlanItemInline(admin.TabularInline):
    model = PlanItem
    extra = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'is_shared', 'likes_count', 'saves_count', 'created_at')
    search_fields = ('title', 'city', 'owner__username', 'share_code')
    list_filter = ('is_shared', 'city_slug', 'created_at')
    inlines = [PlanItemInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'city', 'country', 'is_private', 'allow_friend_requests', 'updated_at')


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'state', 'created_at')


admin.site.register(Friendship)
admin.site.register(PlanItem)
admin.site.register(PlanLike)
admin.site.register(PlanSave)
admin.site.register(PlanJoin)
admin.site.register(PlanComment)
admin.site.register(Conversation)
admin.site.register(Message)
