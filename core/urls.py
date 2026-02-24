from django.urls import path

from core import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('generar/', views.generate_plan_view, name='generate_plan'),
    path('plan/<uuid:plan_id>/', views.plan_results, name='plan_results'),
    path('plan/<uuid:plan_id>/guardar/', views.save_plan, name='save_plan'),
    path('guardados/', views.saved_plans, name='saved_plans'),
    path('guardados/<uuid:plan_id>/', views.plan_detail, name='plan_detail'),
    path('guardados/<uuid:plan_id>/eliminar/', views.delete_plan, name='delete_plan'),
]
