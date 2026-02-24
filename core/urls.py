from django.urls import path

from core import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('api/generate-plan/', views.api_generate_plan, name='api_generate_plan'),
    path('api/save-plan/', views.api_save_plan, name='api_save_plan'),
    path('city/<slug:city_slug>/', views.city_feed, name='city_feed'),
    path('p/<str:share_code>/', views.public_plan_detail, name='public_plan_detail'),
    path('p/<str:share_code>/save', views.save_public_plan, name='save_public_plan'),
    path('plan/<uuid:plan_id>/toggle-public', views.toggle_plan_public, name='toggle_plan_public'),
    path('plan/<uuid:plan_id>/like', views.toggle_plan_like, name='toggle_plan_like'),
    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('my/plans/', views.my_plans, name='my_plans'),
    path('mis-planes/', views.my_plans),
    path('auth/login/', views.AppLoginView.as_view(), name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.AppLogoutView.as_view(), name='logout'),
]
