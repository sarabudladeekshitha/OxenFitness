from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from .models import *
from .forms import *
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Max
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from PIL import Image
import io
import logging
import json

def is_admin(user):
    return user.is_superuser

def is_trainer(user):
    return user.role == 'trainer'

def is_member(user):
    return user.role == 'member'

def home(request):
    return render(request, 'myapp/home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number', '')  # Make phone number optional
        role = request.POST.get('role')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        profile_picture = request.FILES.get('profile_picture')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

       
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            if is_ajax:
                return JsonResponse({'error': 'Passwords do not match.'})
            return redirect('register')

      
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'This email is already registered. Please log in.')
            if is_ajax:
                return JsonResponse({'error': 'This email is already registered. Please log in.'})
            return redirect('register')

   
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'This username is already taken. Please choose another one.')
            if is_ajax:
                return JsonResponse({'error': 'This username is already taken. Please choose another one.'})
            return redirect('register')

       
        try:
            # Case-insensitive email lookup for pre-registration
            pre_registration = PreRegistration.objects.get(
                email__iexact=email,
                is_registered=False,
                role=role
            )
            
            
            if pre_registration.phone_number and phone_number:
                if pre_registration.phone_number != phone_number:
                    messages.error(request, 'Phone number does not match the pre-registered details.')
                    if is_ajax:
                        return JsonResponse({'error': 'Phone number does not match the pre-registered details.'})
                    return redirect('register')
                    
        except PreRegistration.DoesNotExist:
            messages.error(request, 'Your details are not registered. Please contact the Admin to proceed.')
            if is_ajax:
                return JsonResponse({'error': 'Your details are not registered. Please contact the Admin to proceed.'})
            return redirect('register')

        try:
           
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                phone_number=phone_number,
                role=role,
                profile_picture=profile_picture
            )

            
            pre_registration.is_registered = True
            pre_registration.registered_at = timezone.now()
            pre_registration.save()

            
            if role == 'member':
                Member.objects.create(
                    user=user,
                    pre_registration=pre_registration,
                    membership_start_date=timezone.now().date(),
                    membership_end_date=(timezone.now() + timedelta(days=30)).date(),
                    is_active=True
                )
            elif role == 'trainer':
                Trainer.objects.create(
                    user=user,
                    pre_registration=pre_registration,
                    specialization='General Fitness',
                    experience_years=0,
                    bio='New trainer',
                    is_active=True
                )

            
            request.session['registration_success'] = True
            
           
            messages.success(request, 'Registration successful! Please log in with your credentials.')
            
            if is_ajax:
                # For AJAX requests, return a redirect response
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful! Please log in with your credentials.',
                    'redirect': '/login/'
                })
            return redirect('login')
            
        except Exception as e:
         
            logger = logging.getLogger(__name__)
            logger.error(f"Error during registration: {str(e)}")
            
            messages.error(request, 'An error occurred during registration. Please try again or contact support.')
            if is_ajax:
                return JsonResponse({'error': 'An error occurred during registration. Please try again or contact support.'})
            return redirect('register')

    return render(request, 'myapp/register.html')

@login_required
def dashboard(request):
    
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.role == 'trainer':
        return redirect('trainer_dashboard')
    elif request.user.role == 'member':
        return redirect('member_dashboard')
    
    
    context = {
        'user': request.user,
    }
    return render(request, 'myapp/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('login')
   
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    
    total_members = Member.objects.count()
    total_trainers = Trainer.objects.count()
    active_plans = MembershipPlan.objects.count()
    
    
    monthly_revenue = Payment.objects.filter(
        date__month=current_month,
        date__year=current_year,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    
    trainers = Trainer.objects.select_related('user').filter(user__role='trainer').all()
    
    
    members = Member.objects.select_related(
        'user', 
        'membership_plan', 
        'assigned_trainer'
    ).filter(user__role='member').exclude(user__role='admin').all()
    
    
    plans = MembershipPlan.objects.all()
    
   
    member_growth = []
    labels = []
    for i in range(5, -1, -1):
        month = (timezone.now() - timedelta(days=30*i)).month
        year = (timezone.now() - timedelta(days=30*i)).year
        count = Member.objects.filter(
            membership_start_date__month=month,
            membership_start_date__year=year
        ).count()
        member_growth.append(count)
        labels.append(timezone.now() - timedelta(days=30*i))
    
    
    revenue_data = []
    for i in range(5, -1, -1):
        month = (timezone.now() - timedelta(days=30*i)).month
        year = (timezone.now() - timedelta(days=30*i)).year
        amount = Payment.objects.filter(
            date__month=month,
            date__year=year,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_data.append(float(amount))
    
    
    plan_distribution = []
    plan_names = []
    for plan in plans:
        count = Member.objects.filter(membership_plan=plan).count()
        plan_distribution.append(count)
        plan_names.append(plan.name)
    
    context = {
        'total_members': total_members,
        'total_trainers': total_trainers,
        'monthly_revenue': monthly_revenue,
        'active_plans': active_plans,
        'trainers': trainers,
        'members': members,
        'plans': plans,
        'member_growth': member_growth,
        'member_growth_labels': [d.strftime('%b %Y') for d in labels],
        'revenue_data': revenue_data,
        'revenue_labels': [d.strftime('%b %Y') for d in labels],
        'plan_distribution': plan_distribution,
        'plan_names': plan_names,
    }
    
    return render(request, 'myapp/admin_dashboard.html', context)

@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    if request.user.role != 'trainer':
        messages.error(request, 'Access denied. Trainer privileges required.')
        return redirect('login')
    
    trainer = get_object_or_404(Trainer, user=request.user)
    assigned_members = Member.objects.filter(assigned_trainer=trainer)
    
    
    today_sessions_count = TrainingSession.objects.filter(
        trainer=trainer,
        date=datetime.now().date(),
        status='scheduled'
    ).count()
    
    
    active_plans_count = WorkoutPlan.objects.filter(
        trainer=trainer,
        is_active=True
    ).count()
    
    
    total_progress = sum(member.progress for member in assigned_members)
    average_completion_rate = round(total_progress / assigned_members.count()) if assigned_members.count() > 0 else 0
    
   
    workout_plans = WorkoutPlan.objects.filter(
        trainer=trainer
    ).order_by('-created_date')
    
 
    for plan in workout_plans:
        try:
            print(f"Raw exercises data for plan {plan.id}: {plan.exercises}")
            plan.exercises = json.loads(plan.exercises)
            print(f"Parsed exercises data for plan {plan.id}: {plan.exercises}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing exercises data for plan {plan.id}: {e}")
            plan.exercises = {}
    
    
    membership_plans = MembershipPlan.objects.all()
    

    members_with_sessions = assigned_members.annotate(
        last_session_date=Max('trainingsession__date')
    )
    
    context = {
        'assigned_members': members_with_sessions,
        'today_sessions_count': today_sessions_count,
        'active_plans_count': active_plans_count,
        'average_completion_rate': average_completion_rate,
        'workout_plans': workout_plans,
        'membership_plans': membership_plans,
        'today': datetime.now(),
    }
    return render(request, 'myapp/trainer/dashboard.html', context)

@login_required
@user_passes_test(is_member)
def member_dashboard(request):
    if request.user.role != 'member':
        messages.error(request, 'Access denied. Member privileges required.')
        return redirect('login')
    

    member = get_object_or_404(Member, user=request.user)
    

    trainer = member.assigned_trainer
    trainer_info = None
    if trainer:
        trainer_info = {
            'name': trainer.user.get_full_name() or trainer.user.username,
            'email': trainer.user.email,
            'phone': trainer.user.phone_number,
            'specialization': trainer.specialization
        }
    

    workout_plans = WorkoutPlan.objects.filter(
        member=member,
        is_active=True
    ).order_by('-created_date')
    

    for plan in workout_plans:
        try:
            plan.exercises = json.loads(plan.exercises)
            plan.schedule = json.loads(plan.schedule) if plan.schedule else {}
        except (json.JSONDecodeError, TypeError):
            plan.exercises = {}
            plan.schedule = {}
    

    upcoming_sessions = TrainingSession.objects.filter(
        member=member,
        date__gte=timezone.now().date(),
        status='scheduled'
    ).order_by('date', 'time')[:5]
    
    context = {
        'member': member,
        'trainer_info': trainer_info,
        'workout_plans': workout_plans,
        'upcoming_sessions': upcoming_sessions,
        'membership_status': {
            'plan': member.membership_plan,
            'start_date': member.membership_start_date,
            'end_date': member.membership_end_date,
            'is_active': member.is_active,
            'progress': member.progress
        }
    }
    return render(request, 'myapp/member/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def manage_members(request):
    # Get all members with related data
    members = Member.objects.select_related(
        'user',
        'membership_plan',
        'assigned_trainer',
        'assigned_trainer__user'
    ).order_by('-user__date_joined')
    
    # Get all active trainers with their user information
    trainers = Trainer.objects.select_related('user').filter(
        is_active=True,
        user__role='trainer'
    ).order_by('user__first_name', 'user__last_name')
    

    plans = MembershipPlan.objects.all()
    
    context = {
        'members': members,
        'trainers': trainers,
        'plans': plans,
    }
    return render(request, 'myapp/manage_members.html', context)

@login_required
@user_passes_test(is_admin)
def manage_trainers(request):
    if request.method == 'POST':
       
        full_name = request.POST.get('full_name', '').split()
        first_name = full_name[0] if full_name else ''
        last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ''
        email = request.POST.get('email')
        specialization = request.POST.get('specialization')
        experience_years = request.POST.get('experience_years')
        bio = request.POST.get('bio')
        
 
        username = email.split('@')[0]  # Use email prefix as username
        password = User.objects.make_random_password()  # Generate random password
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='trainer'  # Set the role explicitly
        )
        

        trainer = Trainer.objects.create(
            user=user,
            specialization=specialization,
            experience_years=int(experience_years),
            bio=bio,
            is_active=True
        )
        
        messages.success(
            request, 
            f'Trainer added successfully. Username: {username}, Password: {password}'
        )
        return redirect('manage_trainers')
    
    
    trainers = Trainer.objects.select_related('user').filter(user__role='trainer').all()
    return render(request, 'myapp/manage_trainers.html', {'trainers': trainers})

@login_required
@user_passes_test(is_admin)
def manage_plans(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            duration_days = request.POST.get('duration_days')
            features = request.POST.get('features')
            
            # Create new plan
            plan = MembershipPlan.objects.create(
                name=name,
                description=description,
                price=price,
                duration_days=duration_days,
                features=features
            )
            
            messages.success(request, f'Plan "{name}" added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding plan: {str(e)}')
            return redirect('admin_dashboard')
    
    plans = MembershipPlan.objects.all()
    return render(request, 'myapp/manage_plans.html', {'plans': plans})

@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_payments(request):
    # Get all payments
    payments = Payment.objects.all().order_by('-date')
    
    # Get all members for the payment form
    members = Member.objects.all()
    
    # Calculate payment statistics
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get current month's revenue
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_revenue = Payment.objects.filter(
        status='completed',
        date__month=current_month,
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    

    pending_payments = Payment.objects.filter(status='pending').count()
    failed_payments = Payment.objects.filter(status='failed').count()
    
    context = {
        'payments': payments,
        'members': members,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
    }
    
    return render(request, 'myapp/manage_payments.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Payment added successfully.')
            return redirect('manage_payments')
    else:
        form = PaymentForm()
    return render(request, 'myapp/manage_payments.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully.')
            return redirect('manage_payments')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'myapp/manage_payments.html', {'form': form, 'payment': payment})

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully.')
        return redirect('manage_payments')
    return render(request, 'myapp/manage_payments.html', {'payment': payment})

@login_required
@user_passes_test(lambda u: u.is_staff)
def view_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'myapp/manage_payments.html', {'payment': payment})

# Trainer Views
@user_passes_test(is_trainer)
def create_workout_plan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            
            if not member_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Member ID is required'
                }, status=400)
            
            member = get_object_or_404(Member, id=member_id)
            
            # Create workout plan
            workout_plan = WorkoutPlan.objects.create(
                member=member,
                trainer=get_object_or_404(Trainer, user=request.user),
                title=data.get('title', 'Untitled Plan'),
                target_goal=data.get('target_goal', 'General Fitness'),
                duration_weeks=data.get('duration_weeks', 4),
                description=data.get('description', ''),
                exercises=json.dumps(data.get('exercises', {})),
                schedule=json.dumps(data.get('schedule', {})),
                is_active=True
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Workout plan created successfully!',
                'plan_id': workout_plan.id
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    else:
        form = WorkoutPlanForm()
    return render(request, 'myapp/trainer/create_workout_plan.html', {'form': form})

@user_passes_test(is_trainer)
def create_diet_plan(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        if form.is_valid():
            diet_plan = form.save(commit=False)
            diet_plan.member = member
            diet_plan.trainer = get_object_or_404(Trainer, user=request.user)
            diet_plan.save()
            messages.success(request, 'Diet plan created successfully!')
            return redirect('trainer_dashboard')
    else:
        form = DietPlanForm()
    return render(request, 'myapp/trainer/create_diet_plan.html', {'form': form, 'member': member})

# Member Views
@login_required
@user_passes_test(is_member)
def book_session(request):
    member = get_object_or_404(Member, user=request.user)
    trainer = member.assigned_trainer
    
    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration', 60)  # Default 60 minutes
        
        try:
            session = TrainingSession.objects.create(
                member=member,
                trainer=trainer,
                date=date,
                time=time,
                duration_minutes=duration,
                status='scheduled'
            )
            messages.success(request, 'Training session booked successfully!')
            return redirect('member_dashboard')
        except Exception as e:
            messages.error(request, f'Error booking session: {str(e)}')
    
    # Get available time slots for the next 7 days
    available_slots = []
    for i in range(7):
        date = timezone.now().date() + timedelta(days=i)
        # Add your logic here to get available time slots for each date
        # This is a placeholder - you should implement the actual logic
        available_slots.append({
            'date': date,
            'slots': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
        })
    
    context = {
        'member': member,
        'trainer': trainer,
        'available_slots': available_slots
    }
    return render(request, 'myapp/member/book_session.html', context)

@user_passes_test(is_member)
def view_payments(request):
    member = get_object_or_404(Member, user=request.user)
    payments = Payment.objects.filter(member=member).order_by('-payment_date')
    return render(request, 'myapp/member/payments.html', {'payments': payments})

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('contact_us')
    else:
        form = ContactForm()
    return render(request, 'myapp/contact.html', {'form': form})

def about(request):
    return render(request, 'myapp/about.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
    
        print(f"Login attempt for username: {username}")
        
        try:
            user_exists = User.objects.filter(username__iexact=username).exists()
            print(f"User exists: {user_exists}")
 
            if user_exists:
                actual_user = User.objects.get(username__iexact=username)
                username = actual_user.username  
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
            user_exists = False
        
        user = authenticate(request, username=username, password=password)
        print(f"Authentication result: {'Success' if user else 'Failed'}")
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account is inactive. Please contact the administrator.')
                print(f"User {username} is inactive")
            else:
                login(request, user)
                messages.success(request, 'Login successful!')
                print(f"User {username} logged in successfully")

                if user.is_superuser:
                    redirect_url = 'admin_dashboard'
                elif user.role == 'trainer':
                    redirect_url = 'trainer_dashboard'
                elif user.role == 'member':
                    redirect_url = 'member_dashboard'
                else:
                    messages.error(request, 'Invalid user role. Please contact the administrator.')
                    redirect_url = 'login'
                    print(f"User {username} has invalid role: {user.role}")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse(redirect_url)
                    })
                
                return redirect(redirect_url)
        else:
            error_msg = 'Invalid username or password.'
            if not user_exists:
                error_msg = 'Username does not exist.'
            messages.error(request, error_msg)
            print(f"Login failed for {username}: {error_msg}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })

    if request.session.get('registration_success'):
        messages.success(request, 'Registration successful! Please log in with your credentials.')
        del request.session['registration_success']
    
    return render(request, 'myapp/login.html')

def logout_view(request):
    try:
        # Clear the session without requiring database access
        request.session.flush()
        # Logout the user
        logout(request)
        return redirect('login')
    except Exception as e:
        # If there's an error, still try to logout the user
        logout(request)
        return redirect('login')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save to database
        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        # Send email
        try:
            send_mail(
                subject=f'Contact Form: {subject}',
                message=f'From: {name} ({email})\n\nMessage:\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
        
        return redirect('contact')
    
    return render(request, 'myapp/contact.html')

@login_required
@user_passes_test(is_admin)
def manage_pre_registrations(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        
        # Create pre-registration
        pre_registration = PreRegistration.objects.create(
            role=role,
            email=email,
            full_name=full_name
        )
        
        messages.success(
            request, 
            f'Pre-registration created successfully. Unique ID: {pre_registration.unique_id}'
        )
        return redirect('manage_pre_registrations')
    
    # Get all pre-registrations
    pre_registrations = PreRegistration.objects.all().order_by('-created_at')
    
    context = {
        'pre_registrations': pre_registrations,
        'pending_count': PreRegistration.objects.filter(is_registered=False).count(),
        'registered_count': PreRegistration.objects.filter(is_registered=True).count()
    }
    
    return render(request, 'myapp/manage_pre_registrations.html', context)

@login_required
@user_passes_test(is_admin)
def revoke_pre_registration(request, unique_id):
    if request.method == 'POST':
        pre_registration = get_object_or_404(PreRegistration, unique_id=unique_id)
        pre_registration.delete()
        messages.success(request, 'Pre-registration revoked successfully.')
    return redirect('manage_pre_registrations')

@login_required
@user_passes_test(is_admin)
def reset_pre_registration(request, unique_id):
    if request.method == 'POST':
        pre_registration = get_object_or_404(PreRegistration, unique_id=unique_id)
        pre_registration.is_registered = False
        pre_registration.registered_at = None
        pre_registration.save()
        messages.success(request, 'Pre-registration reset successfully.')
    return redirect('manage_pre_registrations')

@login_required
def add_trainer(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add trainers.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            specialization = request.POST.get('specialization')
            experience_years = request.POST.get('experience_years')
            profile_picture = request.FILES.get('profile_picture')
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('add_trainer')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('add_trainer')
            
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='trainer'
            )
            
            # Get or create trainer profile
            trainer, created = Trainer.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': specialization,
                    'experience_years': int(experience_years),
                    'is_active': True
                }
            )
            
            # If trainer already exists, update its fields
            if not created:
                trainer.specialization = specialization
                trainer.experience_years = int(experience_years)
                trainer.is_active = True
                trainer.save()
            
            # Handle profile picture
            if profile_picture:
                trainer.profile_picture = profile_picture
                trainer.save()
            
            messages.success(request, 'Trainer added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding trainer: {str(e)}')
            # Clean up any created objects if there was an error
            if 'user' in locals() and user:
                user.delete()
            return redirect('add_trainer')
    
    # Get all specializations
    specializations = [
        'General Fitness',
        'Weight Training',
        'Cardio',
        'Yoga',
        'Pilates',
        'CrossFit',
        'Sports Training',
        'Nutrition',
        'Rehabilitation',
        'Senior Fitness',
        'Prenatal/Postnatal',
        'Dance Fitness',
        'Martial Arts'
    ]
    
    context = {
        'specializations': specializations
    }
    
    return render(request, 'myapp/admin/add_trainer.html', context)

@login_required
@user_passes_test(is_admin)
def update_trainer_details(request, trainer_id):
    """
    Update trainer details if they're already registered.
    This function allows admins to update trainer information.
    """
    trainer = get_object_or_404(Trainer, id=trainer_id)
    
    if request.method == 'POST':
        try:
            # Update trainer details
            trainer.specialization = request.POST.get('specialization', trainer.specialization)
            trainer.experience_years = request.POST.get('experience_years', trainer.experience_years)
            trainer.bio = request.POST.get('bio', trainer.bio)
            trainer.is_active = request.POST.get('is_active', 'on') == 'on'
            trainer.save()
            
            # Update user details
            user = trainer.user
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            user.save()
            
            messages.success(request, f'Trainer {user.get_full_name() or user.username} updated successfully.')
            return redirect('admin_dashboard')
            
        except Exception as e:
            # Log the error for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating trainer: {str(e)}")
            
            messages.error(request, 'An error occurred while updating the trainer. Please try again.')
            return redirect('admin_dashboard')
    
    context = {
        'trainer': trainer,
        'user': trainer.user,
    }
    return render(request, 'myapp/admin/update_trainer.html', context)

@login_required
def edit_trainer(request, trainer_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit trainers.")
        return redirect('dashboard')
    
    try:
        trainer = Trainer.objects.get(id=trainer_id)
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer not found.")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            # Update trainer profile
            trainer.specialization = request.POST.get('specialization')
            trainer.experience_years = request.POST.get('experience_years')
            trainer.is_active = request.POST.get('is_active') == 'on'
            trainer.save()
            
            # Update assigned members
            assigned_members = request.POST.getlist('assigned_members')
            trainer.assigned_members.set(assigned_members)
            
            messages.success(request, f"Trainer {trainer.user.username} updated successfully!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Trainer {trainer.user.username} updated successfully!",
                    'trainer': {
                        'id': trainer.id,
                        'name': trainer.user.get_full_name() or trainer.user.username,
                        'specialization': trainer.specialization,
                        'assigned_members_count': trainer.assigned_members.count()
                    }
                })
            
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error updating trainer: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f"Error updating trainer: {str(e)}"
                })
            return redirect('edit_trainer', trainer_id=trainer_id)
    
    # Get all active members for the dropdown
    members = Member.objects.filter(is_active=True).select_related('user')
    
    context = {
        'trainer': trainer,
        'members': members,
        'specializations': [
            'General Fitness', 'Weight Training', 'Cardio', 'Yoga', 'CrossFit',
            'Sports Performance', 'Rehabilitation', 'Nutrition', 'Dance Fitness',
            'Senior Fitness', 'Prenatal/Postnatal', 'Martial Arts'
        ]
    }
    
    return render(request, 'myapp/admin/edit_trainer.html', context)

@login_required
def delete_trainer(request, trainer_id):
    if not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Permission denied. Only administrators can delete trainers.'
            }, status=403)
        messages.error(request, 'Permission denied. Only administrators can delete trainers.')
        return redirect('dashboard')
    
    try:
        trainer = Trainer.objects.get(id=trainer_id)
        
        # Unassign all members from this trainer
        Member.objects.filter(assigned_trainer=trainer).update(assigned_trainer=None)
        
        # Delete the trainer's user account
        trainer.user.delete()
        
        # Delete the trainer profile
        trainer.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Trainer deleted successfully.'
            })
        messages.success(request, 'Trainer deleted successfully.')
        
    except Trainer.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Trainer not found.'
            }, status=404)
        messages.error(request, 'Trainer not found.')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': f'Error deleting trainer: {str(e)}'
            }, status=500)
        messages.error(request, f'Error deleting trainer: {str(e)}')
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def add_plan(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            duration_days = request.POST.get('duration_days')
            features = request.POST.get('features')
            
            # Create new plan
            plan = MembershipPlan.objects.create(
                name=name,
                description=description,
                price=price,
                duration_days=duration_days,
                features=features
            )
            
            messages.success(request, f'Plan "{name}" added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding plan: {str(e)}')
            return render(request, 'myapp/add_plan.html')
    
    return render(request, 'myapp/add_plan.html')

@login_required
@user_passes_test(is_admin)
def edit_plan(request, plan_id):
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    
    if request.method == 'POST':
        try:
            plan.name = request.POST.get('name')
            plan.description = request.POST.get('description')
            plan.price = request.POST.get('price')
            plan.duration_days = request.POST.get('duration_days')
            plan.features = request.POST.get('features')
            plan.save()
            
            messages.success(request, f'Plan "{plan.name}" updated successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating plan: {str(e)}')
            return render(request, 'myapp/add_plan.html', {'plan': plan})
    
    return render(request, 'myapp/add_plan.html', {'plan': plan})

@login_required
@user_passes_test(is_admin)
def delete_plan(request, plan_id):
    if request.method == 'POST':
        try:
            plan = get_object_or_404(MembershipPlan, id=plan_id)
            plan_name = plan.name
            plan.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Plan "{plan_name}" deleted successfully!'
            })
        except MembershipPlan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Plan not found.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error deleting plan: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    }, status=400)

@user_passes_test(is_admin)
def add_member(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            plan_id = request.POST.get('membership_plan')
            trainer_id = request.POST.get('assigned_trainer')
            
            # Check if user already exists
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user:
                # Check if user already has a member profile
                if Member.objects.filter(user=existing_user).exists():
                    messages.error(request, 'This user already has a member profile. Please use a different email address.')
                    return redirect('add_member')
                
                # User exists but doesn't have a member profile
                user = existing_user
                # Update user details
                user.phone_number = phone
                if ' ' in name:
                    first_name, last_name = name.rsplit(' ', 1)
                    user.first_name = first_name
                    user.last_name = last_name
                else:
                    user.first_name = name
                user.role = 'member'  # Ensure role is set to member
                user.save()
            else:
                # Create new user account
                username = email  # Using email as username
                password = User.objects.make_random_password()  # Generate random password
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone_number=phone,
                    role='member'
                )
                
                # Set name if provided
                if ' ' in name:
                    first_name, last_name = name.rsplit(' ', 1)
                    user.first_name = first_name
                    user.last_name = last_name
                else:
                    user.first_name = name
                user.save()
            
            # Get related objects
            membership_plan = get_object_or_404(MembershipPlan, id=plan_id) if plan_id else None
            trainer = get_object_or_404(Trainer, id=trainer_id) if trainer_id else None
            
            # Get the member profile (it should be created by the signal)
            member = Member.objects.get(user=user)
            
            # Update the member profile with additional details
            member.membership_plan = membership_plan
            member.assigned_trainer = trainer
            member.membership_start_date = timezone.now().date()
            member.membership_end_date = (timezone.now() + timedelta(days=membership_plan.duration_days if membership_plan else 30)).date()
            member.is_active = True
            member.save()
            
            messages.success(request, f'Member {name} added successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding member: {str(e)}')
            return render(request, 'myapp/add_member.html', {
                'plans': MembershipPlan.objects.all(),
                'trainers': Trainer.objects.all()
            })
    
    # GET request - show the form
    return render(request, 'myapp/add_member.html', {
        'plans': MembershipPlan.objects.all(),
        'trainers': Trainer.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def edit_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    
    if request.method == 'POST':
        try:
            # Update member details
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            plan_id = request.POST.get('membership_plan')
            trainer_id = request.POST.get('assigned_trainer')
            is_active = request.POST.get('is_active') == 'on'
            
            # Update user details
            user = member.user
            if ' ' in name:
                first_name, last_name = name.rsplit(' ', 1)
                user.first_name = first_name
                user.last_name = last_name
            else:
                user.first_name = name
                user.last_name = ''
            
            # Only update email if changed and not already taken
            if email != user.email:
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, 'This email is already taken.')
                    return redirect('edit_member', member_id=member_id)
                user.email = email
            
            user.phone_number = phone
            user.save()
            
            # Update member profile
            member.membership_plan = MembershipPlan.objects.get(id=plan_id) if plan_id else None
            member.assigned_trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
            member.is_active = is_active
            member.save()
            
            messages.success(request, f'Member {name} updated successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating member: {str(e)}')
            return render(request, 'myapp/add_member.html', {
                'member': member,
                'plans': MembershipPlan.objects.all(),
                'trainers': Trainer.objects.all()
            })
    
    # GET request - show the form with member data
    return render(request, 'myapp/add_member.html', {
        'member': member,
        'plans': MembershipPlan.objects.all(),
        'trainers': Trainer.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def delete_member(request, member_id):
    if request.method == 'POST':
        try:
            member = Member.objects.get(id=member_id)
            user = member.user
            
            # Delete member profile and user
            member.delete()
            user.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Member deleted successfully!'
            })
            
        except Member.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Member not found.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error deleting member: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    }, status=400)

@login_required
@user_passes_test(is_trainer)
def add_weight_entry(request, member_id):
    if request.method == 'POST':
        try:
            member = Member.objects.get(id=member_id, assigned_trainer__user=request.user)
            weight = float(request.POST.get('weight'))
            date = request.POST.get('date', datetime.now().date())
            
            weight_entry = WeightEntry.objects.create(
                member=member,
                weight=weight,
                date=date
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Weight entry added successfully',
                'entry': {
                    'id': weight_entry.id,
                    'weight': weight_entry.weight,
                    'date': weight_entry.date.strftime('%Y-%m-%d')
                }
            })
        except (Member.DoesNotExist, ValueError) as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@user_passes_test(is_trainer)
def add_progress_note(request, member_id):
    if request.method == 'POST':
        try:
            member = Member.objects.get(id=member_id, assigned_trainer__user=request.user)
            note = request.POST.get('note')
            
            progress_note = ProgressNote.objects.create(
                member=member,
                trainer=member.assigned_trainer,
                note=note
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Progress note added successfully',
                'note': {
                    'id': progress_note.id,
                    'note': progress_note.note,
                    'date': progress_note.created_at.strftime('%Y-%m-%d %H:%M')
                }
            })
        except Member.DoesNotExist as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@user_passes_test(is_trainer)
def get_member_progress(request, member_id):
    try:
        member = Member.objects.get(id=member_id, assigned_trainer__user=request.user)
        
        # Get weight entries
        weight_entries = WeightEntry.objects.filter(member=member).order_by('date')
        weight_data = [{
            'date': entry.date.strftime('%Y-%m-%d'),
            'weight': entry.weight
        } for entry in weight_entries]
        
        # Get workout plan completion data
        workout_plans = WorkoutPlan.objects.filter(member=member)
        completion_data = {
            'completed': workout_plans.filter(is_active=False).count(),
            'in_progress': workout_plans.filter(is_active=True).count(),
            'total': workout_plans.count()
        }
        
        # Get session attendance data
        sessions = TrainingSession.objects.filter(member=member)
        attendance_data = {
            'attended': sessions.filter(status='completed').count(),
            'missed': sessions.filter(status='cancelled').count(),
            'upcoming': sessions.filter(status='scheduled').count()
        }
        
        # Get progress notes
        notes = ProgressNote.objects.filter(member=member).order_by('-created_at')
        notes_data = [{
            'id': note.id,
            'note': note.note,
            'date': note.created_at.strftime('%Y-%m-%d %H:%M'),
            'trainer': note.trainer.user.get_full_name()
        } for note in notes]
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'weight_data': weight_data,
                'completion_data': completion_data,
                'attendance_data': attendance_data,
                'notes': notes_data
            }
        })
    except Member.DoesNotExist as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@user_passes_test(is_trainer)
def get_workout_plan(request, plan_id):
    try:
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, trainer__user=request.user)
        return JsonResponse({
            'status': 'success',
            'plan': {
                'id': workout_plan.id,
                'title': workout_plan.title,
                'target_goal': workout_plan.target_goal,
                'duration_weeks': workout_plan.duration_weeks,
                'description': workout_plan.description,
                'exercises': json.loads(workout_plan.exercises),
                'schedule': json.loads(workout_plan.schedule),
                'member_id': workout_plan.member.id
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while loading the workout plan'
        }, status=500)

@user_passes_test(is_trainer)
def delete_workout_plan(request, plan_id):
    if request.method != 'DELETE':
        return JsonResponse({
            'status': 'error',
            'message': 'Only DELETE method is allowed'
        }, status=405)
        
    try:
        workout_plan = get_object_or_404(WorkoutPlan, id=plan_id, trainer__user=request.user)
        workout_plan.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Workout plan deleted successfully'
        })
    except WorkoutPlan.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Workout plan not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting workout plan: {str(e)}")  # Add logging
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while deleting the plan'
        }, status=500)
