from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, MembershipPlan, WorkoutPlan, DietPlan, TrainingSession, Contact, Payment, Member

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone_number', 'profile_picture', 'password1', 'password2')

class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = ['name', 'description', 'price', 'duration_days', 'features']

class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['description', 'exercises', 'schedule']

class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['description', 'meal_plan', 'restrictions']

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['date', 'time', 'duration_minutes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['member', 'amount', 'payment_method', 'status', 'transaction_id', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.all().order_by('user__first_name', 'user__last_name')
        self.fields['transaction_id'].required = False
        self.fields['notes'].required = False 