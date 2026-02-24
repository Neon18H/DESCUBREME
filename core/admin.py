from django.contrib import admin

from core.models import Plan, PlanStep


class PlanStepInline(admin.TabularInline):
    model = PlanStep
    extra = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'mood', 'budget_cop', 'created_at', 'is_saved')
    inlines = [PlanStepInline]
