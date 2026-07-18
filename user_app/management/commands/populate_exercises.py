from django.core.management.base import BaseCommand
from user_app.models import Exercise
import pandas as pd
import os
from django.conf import settings
import re


class Command(BaseCommand):
    help = "Populate Exercise model from megaGymDataset.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing exercise data before importing'
        )

    def handle(self, *args, **options):
        if options['clear']:
            Exercise.objects.all().delete()
            self.stdout.write("Cleared existing exercise data")

        # Load CSV data
        csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'megaGymDataset.csv')
        
        try:
            df = pd.read_csv(csv_file_path)
            self.stdout.write(f"Loaded {len(df)} exercises from CSV")
        except FileNotFoundError:
            self.stderr.write("Exercise database file not found!")
            return

        # Clean and process data
        df = df.fillna('')
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)

        created_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            # Map exercise type
            exercise_type = self.map_exercise_type(row.get('Type', ''))
            
            # Map difficulty level
            difficulty_level = self.map_difficulty_level(row.get('Level', ''))
            
            # Generate tags for better search
            tags = self.generate_tags(row)
            
            # Check for compound movements
            is_compound = self.is_compound_movement(row.get('Title', ''), row.get('Desc', ''))
            
            # Check for unilateral movements
            is_unilateral = self.is_unilateral_movement(row.get('Title', ''), row.get('Desc', ''))
            
            # Estimate calories per minute (rough estimation)
            calories_per_minute = self.estimate_calories(row.get('Type', ''), row.get('BodyPart', ''))

            # Create or update exercise
            exercise, created = Exercise.objects.get_or_create(
                title=row.get('Title', '').strip(),
                defaults={
                    'description': row.get('Desc', '').strip(),
                    'exercise_type': exercise_type,
                    'body_part': row.get('BodyPart', '').strip(),
                    'equipment': row.get('Equipment', '').strip(),
                    'difficulty_level': difficulty_level,
                    'rating': row.get('Rating', 0.0),
                    'rating_description': row.get('RatingDesc', '').strip(),
                    'is_compound': is_compound,
                    'is_unilateral': is_unilateral,
                    'estimated_calories_per_minute': calories_per_minute,
                    'tags': tags
                }
            )

            if created:
                created_count += 1
            else:
                # Update existing exercise
                exercise.description = row.get('Desc', '').strip()
                exercise.exercise_type = exercise_type
                exercise.body_part = row.get('BodyPart', '').strip()
                exercise.equipment = row.get('Equipment', '').strip()
                exercise.difficulty_level = difficulty_level
                exercise.rating = row.get('Rating', 0.0)
                exercise.rating_description = row.get('RatingDesc', '').strip()
                exercise.is_compound = is_compound
                exercise.is_unilateral = is_unilateral
                exercise.estimated_calories_per_minute = calories_per_minute
                exercise.tags = tags
                exercise.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed exercises: {created_count} created, {updated_count} updated'
            )
        )

    def map_exercise_type(self, type_str):
        """Map CSV type to model choices"""
        type_lower = type_str.lower()
        if 'strength' in type_lower:
            return 'strength'
        elif 'cardio' in type_lower:
            return 'cardio'
        elif 'flexibility' in type_lower or 'stretch' in type_lower:
            return 'flexibility'
        elif 'plyometric' in type_lower or 'explosive' in type_lower:
            return 'plyometrics'
        elif 'powerlifting' in type_lower:
            return 'powerlifting'
        else:
            return 'strength'  # Default

    def map_difficulty_level(self, level_str):
        """Map CSV level to model choices"""
        level_lower = level_str.lower()
        if 'beginner' in level_lower:
            return 'beginner'
        elif 'intermediate' in level_lower:
            return 'intermediate'
        elif 'advanced' in level_lower:
            return 'advanced'
        else:
            return 'beginner'  # Default

    def generate_tags(self, row):
        """Generate search tags from exercise data"""
        tags = []
        
        # Add body part tags
        if row.get('BodyPart'):
            tags.append(row['BodyPart'].lower())
        
        # Add equipment tags
        if row.get('Equipment'):
            tags.append(row['Equipment'].lower())
        
        # Add type tags
        if row.get('Type'):
            tags.append(row['Type'].lower())
        
        # Extract keywords from title and description
        text = f"{row.get('Title', '')} {row.get('Desc', '')}".lower()
        
        # Common fitness keywords
        keywords = [
            'muscle', 'strength', 'power', 'endurance', 'cardio', 'burn', 'fat',
            'core', 'abs', 'chest', 'back', 'arms', 'legs', 'shoulders',
            'squat', 'press', 'pull', 'push', 'lift', 'curl', 'extend'
        ]
        
        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)
        
        return list(set(tags))  # Remove duplicates

    def is_compound_movement(self, title, description):
        """Determine if this is a compound movement"""
        text = f"{title} {description}".lower()
        compound_indicators = [
            'squat', 'deadlift', 'press', 'pull-up', 'chin-up', 'row',
            'clean', 'snatch', 'thruster', 'burpee', 'lunge'
        ]
        return any(indicator in text for indicator in compound_indicators)

    def is_unilateral_movement(self, title, description):
        """Determine if this is a unilateral movement"""
        text = f"{title} {description}".lower()
        unilateral_indicators = [
            'single', 'one', 'unilateral', 'alternating', 'single-arm', 'single-leg'
        ]
        return any(indicator in text for indicator in unilateral_indicators)

    def estimate_calories(self, exercise_type, body_part):
        """Rough estimation of calories burned per minute"""
        base_calories = {
            'strength': 6.0,
            'cardio': 10.0,
            'flexibility': 3.0,
            'plyometrics': 12.0,
            'powerlifting': 8.0
        }
        
        type_lower = exercise_type.lower()
        if 'strength' in type_lower:
            return base_calories['strength']
        elif 'cardio' in type_lower:
            return base_calories['cardio']
        elif 'flexibility' in type_lower:
            return base_calories['flexibility']
        elif 'plyometric' in type_lower:
            return base_calories['plyometrics']
        else:
            return base_calories['strength']
