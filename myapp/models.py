from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('trainer', 'Trainer'),
        ('member', 'Member'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

# Signal to create Trainer/Member objects when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'trainer':
            Trainer.objects.create(
                user=instance,
                specialization='General Fitness',  # Default value
                experience_years=0,  # Default value
                bio='New trainer',  # Default value
                is_active=True
            )
        elif instance.role == 'member':
            Member.objects.create(
                user=instance,
                membership_start_date=timezone.now().date(),
                membership_end_date=(timezone.now() + timezone.timedelta(days=30)).date(),
                is_active=True
            )

class PreRegistration(models.Model):
    ROLE_CHOICES = (
        ('trainer', 'Trainer'),
        ('member', 'Member'),
    )
    unique_id = models.CharField(max_length=8, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField()
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)
    is_registered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.unique_id} ({'Registered' if self.is_registered else 'Pending'})"

class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    features = models.TextField()

    def __str__(self):
        return self.name

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pre_registration = models.OneToOneField(PreRegistration, on_delete=models.SET_NULL, null=True)
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    assigned_trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    membership_start_date = models.DateField()
    membership_end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    progress = models.IntegerField(default=0, help_text='Overall progress percentage')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pre_registration = models.OneToOneField(PreRegistration, on_delete=models.SET_NULL, null=True)
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField()
    bio = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.specialization}"

class WorkoutPlan(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    created_date = models.DateField(auto_now_add=True)
    description = models.TextField()
    exercises = models.TextField()
    schedule = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=100, default='Untitled Plan')
    target_goal = models.CharField(max_length=50, default='General Fitness')
    duration_weeks = models.IntegerField(default=4)

    def __str__(self):
        return f"Workout Plan for {self.member.user.username}"

class DietPlan(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True)
    created_date = models.DateField(auto_now_add=True)
    description = models.TextField()
    meal_plan = models.TextField()
    restrictions = models.TextField()

    def __str__(self):
        return f"Diet Plan for {self.member.user.username}"

class TrainingSession(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.IntegerField()
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')

    def __str__(self):
        return f"Training Session: {self.member.user.username} with {self.trainer.user.username}"

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    )
    
    PAYMENT_METHODS = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    )
    
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.member.user.get_full_name()} - ${self.amount} ({self.status})"

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attendance: {self.user.username} - {self.check_in.date()}"

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

class WeightEntry(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Weight Entries'
    
    def __str__(self):
        return f"{self.member.user.username} - {self.weight}kg on {self.date}"

class ProgressNote(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.member.user.username} by {self.trainer.user.username}"
