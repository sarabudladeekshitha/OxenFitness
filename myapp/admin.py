from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Member, Trainer, MembershipPlan, WorkoutPlan, DietPlan, TrainingSession, Payment, PreRegistration

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_plan', 'assigned_trainer', 'membership_start_date', 'membership_end_date', 'is_active')
    list_filter = ('is_active', 'membership_plan', 'assigned_trainer')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user', 'membership_plan', 'assigned_trainer')

class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'is_active')
    list_filter = ('is_active', 'specialization')
    search_fields = ('user__username', 'user__email', 'specialization')
    raw_id_fields = ('user',)

class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
    search_fields = ('name',)

class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('member', 'trainer', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('member__user__username', 'trainer__user__username')
    raw_id_fields = ('member', 'trainer')

class DietPlanAdmin(admin.ModelAdmin):
    list_display = ('member', 'trainer', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('member__user__username', 'trainer__user__username')
    raw_id_fields = ('member', 'trainer')

class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('member', 'trainer', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('member__user__username', 'trainer__user__username')
    raw_id_fields = ('member', 'trainer')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'date', 'status', 'payment_method')
    list_filter = ('status', 'payment_method', 'date')
    search_fields = ('member__user__username', 'transaction_id')
    raw_id_fields = ('member',)

class PreRegistrationAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'full_name', 'email', 'role', 'is_registered', 'created_at')
    list_filter = ('role', 'is_registered')
    search_fields = ('unique_id', 'full_name', 'email')
    readonly_fields = ('unique_id',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Trainer, TrainerAdmin)
admin.site.register(MembershipPlan, MembershipPlanAdmin)
admin.site.register(WorkoutPlan, WorkoutPlanAdmin)
admin.site.register(DietPlan, DietPlanAdmin)
admin.site.register(TrainingSession, TrainingSessionAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(PreRegistration, PreRegistrationAdmin)
