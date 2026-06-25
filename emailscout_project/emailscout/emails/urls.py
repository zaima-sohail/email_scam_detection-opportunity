from django.urls import path
from . import views

urlpatterns = [
    # HTML pages
    path('', views.email_list, name='email_list'),
    path('<int:email_id>/', views.email_detail, name='email_detail'),
    path('fetch/', views.fetch_emails, name='fetch_emails'),
    path('security-report/', views.security_report, name='security_report'),
    path('opportunities/', views.opportunities_board, name='opportunities_board'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),

    # JSON API (for other members to use)
    path('api/list/', views.api_email_list, name='api_email_list'),
    path('api/<int:email_id>/', views.api_email_detail, name='api_email_detail'),
    path('api/<int:email_id>/update/', views.api_update_email, name='api_update_email'),
    path('api/<int:email_id>/flag/', views.api_flag_email, name='api_flag_email'),
    path('api/flagged/', views.api_flagged_emails, name='api_flagged_emails'),
    path('api/scam-stats/', views.api_scam_statistics, name='api_scam_statistics'),
]
