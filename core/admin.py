from django.contrib import admin

from core.models import Plan, PlanItem, PlanLike, PlanSave, UserProfile


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
    list_display = ('user', 'display_name', 'city_default', 'updated_at')
    search_fields = ('user__username', 'display_name', 'city_default')


admin.site.register(PlanItem)
admin.site.register(PlanLike)
admin.site.register(PlanSave)
