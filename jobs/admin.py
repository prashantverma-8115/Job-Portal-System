from django.contrib import admin
from .models import Job, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'location',
        'job_type',
        'is_active',
        'created_at',
    )

    search_fields = ('title', 'company', 'location')

    list_filter = ('job_type', 'is_active')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'candidate',
        'job',
        'status',
        'applied_at',
    )

    search_fields = (
        'candidate__username',
        'job__title',
    )

    list_filter = ('status', 'applied_at')
