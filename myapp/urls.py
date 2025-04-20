from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/member/', views.member_dashboard, name='member_dashboard'),
    path('dashboard/member/book-session/', views.book_session, name='book_session'),
    path('dashboard/trainer/', views.trainer_dashboard, name='trainer_dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/members/', views.manage_members, name='manage_members'),
    path('dashboard/admin/members/add/', views.add_member, name='add_member'),
    path('dashboard/admin/members/<int:member_id>/edit/', views.edit_member, name='edit_member'),
    path('dashboard/admin/members/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    path('dashboard/admin/trainers/', views.manage_trainers, name='manage_trainers'),
    path('dashboard/admin/plans/', views.manage_plans, name='manage_plans'),
    path('dashboard/admin/payments/', views.manage_payments, name='manage_payments'),
    path('dashboard/admin/payments/add/', views.add_payment, name='add_payment'),
    path('dashboard/admin/payments/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('dashboard/admin/payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    path('dashboard/admin/payments/<int:payment_id>/view/', views.view_payment, name='view_payment'),
    
 
    path('dashboard/admin/pre-registrations/', views.manage_pre_registrations, name='manage_pre_registrations'),
    path('dashboard/admin/pre-registrations/<str:unique_id>/revoke/', views.revoke_pre_registration, name='revoke_pre_registration'),
    path('dashboard/admin/pre-registrations/<str:unique_id>/reset/', views.reset_pre_registration, name='reset_pre_registration'),
    
    
    path('dashboard/admin/trainers/add/', views.add_trainer, name='add_trainer'),
    path('dashboard/admin/trainers/<int:trainer_id>/edit/', views.edit_trainer, name='edit_trainer'),
    path('dashboard/admin/trainers/<int:trainer_id>/update/', views.update_trainer_details, name='update_trainer_details'),
    path('dashboard/admin/trainers/<int:trainer_id>/delete/', views.delete_trainer, name='delete_trainer'),
    path('dashboard/admin/plans/', views.manage_plans, name='manage_plans'),
    path('dashboard/admin/plans/add/', views.add_plan, name='add_plan'),
    path('dashboard/admin/plans/<int:plan_id>/edit/', views.edit_plan, name='edit_plan'),
    path('dashboard/admin/plans/<int:plan_id>/delete/', views.delete_plan, name='delete_plan'),
    
    
    path('api/member/<int:member_id>/weight/', views.add_weight_entry, name='add_weight_entry'),
    path('api/member/<int:member_id>/note/', views.add_progress_note, name='add_progress_note'),
    path('api/member/<int:member_id>/progress/', views.get_member_progress, name='get_member_progress'),
    
   
    path('create-workout-plan/', views.create_workout_plan, name='create_workout_plan'),
    path('workout-plan/<int:plan_id>/', views.get_workout_plan, name='get_workout_plan'),
    path('workout-plan/<int:plan_id>/delete/', views.delete_workout_plan, name='delete_workout_plan'),
] 