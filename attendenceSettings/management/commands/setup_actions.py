from django.core.management.base import BaseCommand
from attendenceSettings.models import Action

class Command(BaseCommand):
    help = 'Create default actions for the attendance system'

    def handle(self, *args, **options):
        default_actions = [
            {"name": "Check In", "code": "check_in", "description": "Employee check-in"},
            {"name": "Check Out", "code": "check_out", "description": "Employee check-out"},
            {"name": "Break Start", "code": "break_start", "description": "Start of break time"},
            {"name": "Break End", "code": "break_end", "description": "End of break time"},
            {"name": "Lunch Start", "code": "lunch_start", "description": "Start of lunch break"},
            {"name": "Lunch End", "code": "lunch_end", "description": "End of lunch break"},
            {"name": "Half Day", "code": "half_day", "description": "Half day attendance"},
            {"name": "Work From Home", "code": "wfh", "description": "Work from home"},
            {"name": "Meeting", "code": "meeting", "description": "In meeting"},
            {"name": "Training", "code": "training", "description": "In training session"},
        ]
        
        created_count = 0
        for action_data in default_actions:
            action, created = Action.objects.get_or_create(
                code=action_data["code"],
                defaults={
                    "name": action_data["name"],
                    "description": action_data["description"],
                    "is_active": True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created action: {action.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Action already exists: {action.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new actions')
        ) 