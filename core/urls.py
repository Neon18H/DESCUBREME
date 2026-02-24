from django.urls import path

from core import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('api/generate-plan/', views.api_generate_plan, name='api_generate_plan'),
    path('api/save-plan/', views.api_save_plan, name='api_save_plan'),
    path('people/', views.people_list, name='people_list'),
    path('city/<slug:city_slug>/', views.city_feed, name='city_feed'),
    path('p/<uuid:plan_id>/', views.public_plan_detail, name='public_plan_detail'),
    path('p/<uuid:plan_id>/save', views.save_public_plan, name='save_public_plan'),
    path('p/<uuid:plan_id>/join/', views.plan_join, name='plan_join'),
    path('p/<uuid:plan_id>/unjoin/', views.plan_unjoin, name='plan_unjoin'),
    path('p/<uuid:plan_id>/comment/', views.plan_comment, name='plan_comment'),
    path('p/<uuid:plan_id>/share/', views.toggle_plan_public, name='plan_share'),
    path('plan/<uuid:plan_id>/toggle-public', views.toggle_plan_public, name='toggle_plan_public'),
    path('plan/<uuid:plan_id>/like', views.toggle_plan_like, name='toggle_plan_like'),

    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('settings/profile/', views.profile_edit, name='profile_edit'),

    path('friends/request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friends/', views.friends_list, name='friends_list'),

    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<str:username>/', views.chat_thread, name='chat_thread'),
    path('chat/<str:username>/send/', views.chat_send, name='chat_send'),
    path('chat/<str:username>/poll/', views.chat_poll, name='chat_poll'),

    path('my/plans/', views.my_plans, name='my_plans'),
    path('mis-planes/', views.my_plans),
    path('auth/login/', views.AppLoginView.as_view(), name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.AppLogoutView.as_view(), name='logout'),
]
