from django.core.management.base import BaseCommand
from myapp.models import WorkoutPlan
import json

class Command(BaseCommand):
    help = 'Check workout plans and their exercises data'

    def handle(self, *args, **options):
        workout_plans = WorkoutPlan.objects.all()
        self.stdout.write(f"Found {workout_plans.count()} workout plans")
        
        for plan in workout_plans:
            self.stdout.write(f"\nWorkout Plan ID: {plan.id}")
            self.stdout.write(f"Title: {plan.title}")
            self.stdout.write(f"Member: {plan.member.user.username}")
            self.stdout.write(f"Raw exercises data: {plan.exercises}")
            
            try:
                parsed_exercises = json.loads(plan.exercises)
                self.stdout.write(f"Parsed exercises data: {parsed_exercises}")
            except (json.JSONDecodeError, TypeError) as e:
                self.stdout.write(f"Error parsing exercises data: {e}") 