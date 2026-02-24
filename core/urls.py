from django.urls import path

from core import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('generate/', views.generate_plan_view, name='generate_plan'),
    path('plan/<uuid:plan_id>/', views.plan_results, name='plan_results'),
    path('plan/<uuid:plan_id>/save/', views.save_plan, name='save_plan'),
    path('saved/', views.saved_plans, name='saved_plans'),
    path('saved/<uuid:plan_id>/', views.plan_detail, name='plan_detail'),
    path('saved/<uuid:plan_id>/delete/', views.delete_plan, name='delete_plan'),
    path('auth/login/', views.AppLoginView.as_view(), name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.AppLogoutView.as_view(), name='logout'),
]
