from django.urls import path

from core import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('api/generate-plan/', views.api_generate_plan, name='api_generate_plan'),
    path('api/save-place/', views.api_save_place, name='api_save_place'),
    path('mis-planes/', views.my_plans, name='my_plans'),
    path('mis-planes/<uuid:plan_id>/delete/', views.delete_favorite_plan, name='delete_favorite_plan'),
    path('auth/login/', views.AppLoginView.as_view(), name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.AppLogoutView.as_view(), name='logout'),
]
