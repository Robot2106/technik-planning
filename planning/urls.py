from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Mitarbeiter Dashboard
    path('', views.dashboard, name='dashboard'),
    path('mein-profil/', views.my_profile, name='my_profile'),
    path('meine-verfügbarkeiten/', views.my_availabilities, name='my_availabilities'),
    path('mein-einsatzplan/', views.my_schedule, name='my_schedule'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Terminverwaltung
    path('termine/', views.event_list, name='event_list'),
    path('termine/neu/', views.event_create, name='event_create'),
    path('termine/<int:pk>/', views.event_detail, name='event_detail'),
    path('termine/<int:pk>/bearbeiten/', views.event_update, name='event_update'),
    path('termine/<int:pk>/löschen/', views.event_delete, name='event_delete'),
    path('termine/<int:pk>/freigeben/', views.release_event_for_signup, name='release_event'),
    path('termine/<int:pk>/auto-zuteilung/', views.auto_assign, name='auto_assign'),
    path('termine/export-csv/', views.event_export_csv, name='event_export_csv'),
    
    # Admin-Verwaltung
    path('admin/benutzer/', views.user_management, name='user_management'),
    path('admin/statistiken/', views.statistics, name='statistics'),
]
