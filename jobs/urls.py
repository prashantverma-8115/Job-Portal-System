from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path(
        'recruiter/dashboard/',
        views.recruiter_dashboard,
        name='recruiter_dashboard'
    ),
    path(
        'recruiter/jobs/create/',
        views.job_create,
        name='job_create'
    ),
    path(
        'recruiter/applications/',
        views.recruiter_applications,
        name='recruiter_applications'
    ),
    path(
        'recruiter/applications/<int:application_id>/update/',
        views.update_application_status,
        name='update_application_status'
    ),

    path(
        'my-applications/',
        views.my_applications,
        name='my_applications'
    ),
]
