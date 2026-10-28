from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError

from .forms import RegisterForm, JobForm
from .models import Job, UserProfile, JobApplication


# Show all active jobs and search/filter jobs
def job_list(request):
    jobs = Job.objects.filter(
        is_active=True
    ).order_by('-created_at')

    keyword = request.GET.get('q', '').strip()

    if keyword:
        jobs = jobs.filter(
            title__icontains=keyword
        ) | jobs.filter(
            company__icontains=keyword
        ) | jobs.filter(
            location__icontains=keyword
        )

    job_type = request.GET.get('job_type', '').strip()

    if job_type:
        jobs = jobs.filter(job_type__iexact=job_type)

    return render(
        request,
        'jobs/job_list.html',
        {
            'jobs': jobs,
            'keyword': keyword,
            'selected_job_type': job_type,
        }
    )


# Job details and candidate job application
@login_required
def job_detail(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )

    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    has_applied = JobApplication.objects.filter(
        candidate=request.user,
        job=job
    ).exists()

    if request.method == 'POST':
        if profile is None or profile.role != 'candidate':
            raise PermissionDenied(
                'Only candidates can apply for jobs.'
            )

        if has_applied:
            messages.warning(
                request,
                'You have already applied for this job.'
            )
        else:
            try:
                JobApplication.objects.create(
                    candidate=request.user,
                    job=job
                )

                messages.success(
                    request,
                    'Your application has been submitted successfully!'
                )

            except IntegrityError:
                messages.warning(
                    request,
                    'You have already applied for this job.'
                )

        return redirect('job_detail', job_id=job.id)

    return render(
        request,
        'jobs/job_detail.html',
        {
            'job': job,
            'has_applied': has_applied,
            'profile': profile,
        }
    )


# Register candidate or recruiter
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )

                UserProfile.objects.create(
                    user=user,
                    role=form.cleaned_data['role']
                )

                messages.success(
                    request,
                    'Your account has been created successfully.'
                )

                return redirect('login')

            except IntegrityError:
                form.add_error(
                    'username',
                    'This username is already registered.'
                )

    else:
        form = RegisterForm()

    return render(
        request,
        'jobs/register.html',
        {'form': form}
    )


# User login
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            messages.success(
                request,
                'Login successful!'
            )

            return redirect('job_list')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(
        request,
        'jobs/login.html'
    )


# User logout
def user_logout(request):
    logout(request)

    messages.success(
        request,
        'You have logged out successfully.'
    )

    return redirect('job_list')


# Recruiter dashboard
@login_required
def recruiter_dashboard(request):
    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != 'recruiter':
        raise PermissionDenied(
            'Only recruiters can access this page.'
        )

    jobs = Job.objects.filter(
        posted_by=request.user
    ).order_by('-created_at')

    return render(
        request,
        'jobs/recruiter_dashboard.html',
        {'jobs': jobs}
    )


# Recruiter creates a job
@login_required
def job_create(request):
    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != 'recruiter':
        raise PermissionDenied(
            'Only recruiters can post jobs.'
        )

    if request.method == 'POST':
        form = JobForm(request.POST)

        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()

            messages.success(
                request,
                'Job posted successfully!'
            )

            return redirect('recruiter_dashboard')

    else:
        form = JobForm()

    return render(
        request,
        'jobs/job_form.html',
        {'form': form}
    )


# Candidate views their own applications
@login_required
def my_applications(request):
    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != 'candidate':
        raise PermissionDenied(
            'Only candidates can view their applications.'
        )

    applications = JobApplication.objects.filter(
        candidate=request.user
    ).select_related(
        'job'
    ).order_by('-applied_at')

    return render(
        request,
        'jobs/my_applications.html',
        {'applications': applications}
    )


# Recruiter views applications for their own jobs
@login_required
def recruiter_applications(request):
    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != 'recruiter':
        raise PermissionDenied(
            'Only recruiters can view applications.'
        )

    applications = JobApplication.objects.filter(
        job__posted_by=request.user
    ).select_related(
        'candidate',
        'job'
    ).order_by('-applied_at')

    # Debugging: these messages appear in the terminal
    print('Logged-in recruiter:', request.user.username)
    print('Recruiter role:', profile.role)
    print('Applications found:', applications.count())

    return render(
        request,
        'jobs/recruiter_applications.html',
        {'applications': applications}
    )


# Recruiter updates an application's status
@login_required
def update_application_status(request, application_id):
    if request.method != 'POST':
        return redirect('recruiter_applications')

    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != 'recruiter':
        raise PermissionDenied(
            'Only recruiters can update application status.'
        )

    application = get_object_or_404(
        JobApplication,
        id=application_id,
        job__posted_by=request.user
    )

    status = request.POST.get('status', '')

    if status not in ['Pending', 'Accepted', 'Rejected']:
        messages.error(
            request,
            'Invalid application status.'
        )

        return redirect('recruiter_applications')

    application.status = status
    application.save(
        update_fields=['status']
    )

    messages.success(
        request,
        'Application status updated successfully.'
    )

    return redirect('recruiter_applications')
