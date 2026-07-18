from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_app.models import WorkoutPlan
import pandas as pd
import os
from django.conf import settings
import random
import json

User = get_user_model()


class Command(BaseCommand):
    help = "Create AI-powered workout plans based on exercise database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of workout plans to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create admin user
        try:
            admin = User.objects.get(username="admin")
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                email="admin@fitness.com",
                username="admin",
                password="adminpass123"
            )
            self.stdout.write("Created admin user")

        # Load exercise data
        csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'megaGymDataset.csv')
        
        try:
            df = pd.read_csv(csv_file_path)
            self.stdout.write(f"Loaded {len(df)} exercises from database")
        except FileNotFoundError:
            self.stderr.write("Exercise database file not found!")
            return

        # Clean data
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
        df = df.fillna('')

        # Define workout plan templates
        workout_templates = [
            {
                'title': 'Beginner Full Body Strength',
                'description': 'A comprehensive full-body workout designed for beginners focusing on fundamental movements and building base strength.',
                'target_body_parts': ['Chest', 'Back', 'Shoulders', 'Legs', 'Abdominals'],
                'equipment': ['Dumbbell', 'Barbell', 'Bodyweight'],
                'level': 'Beginner',
                'duration': 45,
                'age_min': 18,
                'age_max': 65
            },
            {
                'title': 'Advanced HIIT Cardio Blast',
                'description': 'High-intensity interval training designed to maximize calorie burn and improve cardiovascular fitness.',
                'target_body_parts': ['Abdominals', 'Legs', 'Full Body'],
                'equipment': ['Bodyweight', 'Kettlebells'],
                'level': 'Advanced',
                'duration': 30,
                'age_min': 20,
                'age_max': 50
            },
            {
                'title': 'Intermediate Upper Body Power',
                'description': 'Focus on building upper body strength and muscle mass with compound and isolation movements.',
                'target_body_parts': ['Chest', 'Back', 'Shoulders', 'Arms'],
                'equipment': ['Dumbbell', 'Barbell', 'Cable'],
                'level': 'Intermediate',
                'duration': 60,
                'age_min': 16,
                'age_max': 60
            },
            {
                'title': 'Core Stability & Flexibility',
                'description': 'Develop core strength, stability, and improve overall flexibility and mobility.',
                'target_body_parts': ['Abdominals', 'Back'],
                'equipment': ['Bodyweight', 'Bands', 'Exercise Ball'],
                'level': 'Beginner',
                'duration': 35,
                'age_min': 15,
                'age_max': 70
            },
            {
                'title': 'Lower Body Strength Builder',
                'description': 'Comprehensive lower body workout targeting glutes, quads, hamstrings, and calves.',
                'target_body_parts': ['Legs', 'Glutes'],
                'equipment': ['Dumbbell', 'Barbell', 'Bodyweight'],
                'level': 'Intermediate',
                'duration': 50,
                'age_min': 18,
                'age_max': 55
            },
            {
                'title': 'Fat Burning Circuit',
                'description': 'High-energy circuit training designed to maximize fat loss while preserving muscle mass.',
                'target_body_parts': ['Full Body', 'Abdominals'],
                'equipment': ['Kettlebells', 'Dumbbell', 'Bodyweight'],
                'level': 'Intermediate',
                'duration': 40,
                'age_min': 20,
                'age_max': 50
            },
            {
                'title': 'Functional Movement Training',
                'description': 'Improve daily movement patterns and functional strength for real-world activities.',
                'target_body_parts': ['Full Body', 'Core'],
                'equipment': ['Bodyweight', 'Kettlebells', 'Bands'],
                'level': 'Beginner',
                'duration': 45,
                'age_min': 25,
                'age_max': 65
            },
            {
                'title': 'Athletic Performance Enhancement',
                'description': 'Sport-specific training to improve power, agility, and athletic performance.',
                'target_body_parts': ['Full Body', 'Legs', 'Core'],
                'equipment': ['Barbell', 'Dumbbell', 'Plyometric'],
                'level': 'Advanced',
                'duration': 75,
                'age_min': 18,
                'age_max': 35
            }
        ]

        created_count = 0

        for i in range(count):
            # Select a template (cycle through them)
            template = workout_templates[i % len(workout_templates)]
            
            # Find exercises matching the template
            matching_exercises = df[
                (df['BodyPart'].str.contains('|'.join(template['target_body_parts']), case=False, na=False)) |
                (df['Equipment'].str.contains('|'.join(template['equipment']), case=False, na=False)) |
                (df['Level'].str.contains(template['level'], case=False, na=False))
            ]

            if len(matching_exercises) < 3:
                # If not enough matching exercises, use any exercises
                matching_exercises = df.sample(n=min(8, len(df)))

            # Select 4-8 exercises for the workout
            num_exercises = random.randint(4, 8)
            selected_exercises = matching_exercises.sample(n=min(num_exercises, len(matching_exercises)))

            # Create workout steps
            steps = []
            for idx, (_, exercise) in enumerate(selected_exercises.iterrows()):
                step = {
                    "order": idx + 1,
                    "guide": f"{exercise['Title']}: {exercise['Desc'][:100]}..." if len(exercise['Desc']) > 100 else exercise['Desc'],
                    "duration": random.randint(30, 180),  # 30 seconds to 3 minutes
                    "sets": random.randint(2, 4),
                    "reps": f"{random.randint(8, 15)}-{random.randint(16, 25)}",
                    "equipment": exercise['Equipment'],
                    "body_part": exercise['BodyPart'],
                    "level": exercise['Level']
                }
                steps.append(step)

            # Create variation in title
            variation_number = (i // len(workout_templates)) + 1
            if variation_number > 1:
                title = f"{template['title']} v{variation_number}"
            else:
                title = template['title']

            # Create the workout plan
            workout_plan = WorkoutPlan.objects.create(
                title=title,
                description=template['description'],
                created_by=admin,
                is_paid=random.choice([True, False]),  # Random paid/free
                workout_duration=template['duration'],
                recommended_age_min=template['age_min'],
                recommended_age_max=template['age_max'],
                steps=steps
            )

            created_count += 1
            self.stdout.write(f"Created workout plan: {title}")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} AI-powered workout plans!')
        )
