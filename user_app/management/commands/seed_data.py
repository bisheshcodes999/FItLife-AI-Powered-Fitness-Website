import random
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_app.models import WorkoutPlan, MealPlan, SuccessStory

User = get_user_model()

class Command(BaseCommand):
    help = "Seed database with 5 workout plans, 5 meal plans, and 5 success stories"

    def handle(self, *args, **kwargs):
        # Clear existing data
        WorkoutPlan.objects.all().delete()
        MealPlan.objects.all().delete()
        SuccessStory.objects.all().delete()
        self.stdout.write("Cleared existing WorkoutPlan, MealPlan, and SuccessStory data.")

        # Create admin user with proper unique constraints
        try:
            admin = User.objects.get(username="admin")
            self.stdout.write("Admin user already exists")
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                email="admin@fitness.com",
                username="admin",
                password="adminpass123",
            )
            admin.is_active = True
            admin.save()
            self.stdout.write("Created admin user")

        # Image links arrays
        WORKOUT_THUMBNAILS = [
            "https://images.unsplash.com/photo-1571019614242-c955c175d3f3",
            "https://images.unsplash.com/photo-1534258936925-c58bed479fc3",
            "https://images.unsplash.com/photo-1581009137042-c552e485697a",
            "https://images.unsplash.com/photo-1517343985841-f8b2d66e010b",
            "https://images.unsplash.com/photo-1576678927484-cc907957088c",
        ]

        MEAL_IMAGES = [
            "https://images.unsplash.com/photo-1498837167922-ddd27525d352",
            "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe",
            "https://images.unsplash.com/photo-1467003909585-2f8a72700288",
            "https://images.unsplash.com/photo-1482049016688-2d3e1b311543",
            "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
        ]

        SUCCESS_IMAGES = [
            "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91",
            "https://images.unsplash.com/photo-1541532713592-79a0317b6b77",
            "https://images.unsplash.com/photo-1549068106-b024baf5062d",
            "https://images.unsplash.com/photo-1581044777550-4cfa60707c03",
            "https://images.unsplash.com/photo-1545175707-9eec1209f720",
        ]

        # -------------------------------
        # Seed 5 Workout Plans
        # -------------------------------
        workout_data = [
            {
                "title": "Chest Workout Supreme",
                "description": "A focused chest workout plan for strength and definition.",
                "steps": [
                    {
                        "order": 1,
                        "guide": "Warm-up: 5 minutes jogging",
                        "duration": 5,
                        "image": "https://images.app.goo.gl/QaRr4u2gykZnfETP6",
                    },
                    {
                        "order": 2,
                        "guide": "Bench Press: 3 sets of 10 reps",
                        "duration": 15,
                        "image": "https://images.unsplash.com/photo-1583454110557-83bd23aef695",
                        "youtube_link": "https://youtu.be/benchpress"
                    },
                    {
                        "order": 3,
                        "guide": "Dumbbell Flyes: 3 sets of 12 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1560347876-aeef00ee58a1",
                        "youtube_link": "https://youtu.be/dumbbellflyes"
                    },
                    {
                        "order": 4,
                        "guide": "Push-ups: 3 sets until failure",
                        "duration": 8,
                        "image": "https://images.unsplash.com/photo-1526401485004-6cfd9bf36f8e",
                        "youtube_link": "https://youtu.be/pushups"
                    },
                    {
                        "order": 5,
                        "guide": "Cool Down: 5 minutes stretching",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
                        "youtube_link": "https://youtu.be/cooldown"
                    },
                ]
            },
            {
                "title": "Leg Workout Intense",
                "description": "A comprehensive leg workout plan for building lower body strength.",
                "steps": [
                    {
                        "order": 1,
                        "guide": "Warm-up: 5 minutes brisk walk",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1571019614242-c955c175d3f3",
                        "youtube_link": "https://youtu.be/warmupleg"
                    },
                    {
                        "order": 2,
                        "guide": "Squats: 4 sets of 12 reps",
                        "duration": 15,
                        "image": "https://images.unsplash.com/photo-1534258936925-c58bed479fc3",
                        "youtube_link": "https://youtu.be/squats"
                    },
                    {
                        "order": 3,
                        "guide": "Lunges: 3 sets of 15 reps per leg",
                        "duration": 15,
                        "image": "https://images.unsplash.com/photo-1581009137042-c552e485697a",
                        "youtube_link": "https://youtu.be/lunges"
                    },
                    {
                        "order": 4,
                        "guide": "Leg Press: 3 sets of 10 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1576678927484-cc907957088c",
                        "youtube_link": "https://youtu.be/legpress"
                    },
                    {
                        "order": 5,
                        "guide": "Cool Down: 5 minutes stretching",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
                        "youtube_link": "https://youtu.be/cooldownleg"
                    },
                ]
            },
            {
                "title": "Arm & Shoulder Workout",
                "description": "Target your arms and shoulders with this effective workout plan.",
                "steps": [
                    {
                        "order": 1,
                        "guide": "Warm-up: 5 minutes jump rope",
                        "duration": 5,
                        "image": "https://images.app.goo.gl/QaRr4u2gykZnfETP6",
                    },
                    {
                        "order": 2,
                        "guide": "Bicep Curls: 3 sets of 12 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1560347876-aeef00ee58a1",
                        "youtube_link": "https://youtu.be/bicepcurls"
                    },
                    {
                        "order": 3,
                        "guide": "Tricep Dips: 3 sets of 15 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1526401485004-6cfd9bf36f8e",
                        "youtube_link": "https://youtu.be/tricepdips"
                    },
                    {
                        "order": 4,
                        "guide": "Shoulder Press: 3 sets of 10 reps",
                        "duration": 12,
                        "image": "https://images.unsplash.com/photo-1517638851339-4e76af50a6f3",
                        "youtube_link": "https://youtu.be/shoulderpress"
                    },
                    {
                        "order": 5,
                        "guide": "Cool Down: 5 minutes stretching",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
                        "youtube_link": "https://youtu.be/cooldownarm"
                    },
                ]
            },
            {
                "title": "Back Workout Power",
                "description": "Improve your back strength and posture with this essential workout plan.",
                "steps": [
                    {
                        "order": 1,
                        "guide": "Warm-up: 5 minutes rowing",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1534258936925-c58bed479fc3",
                        "youtube_link": "https://youtu.be/rowingwarmup"
                    },
                    {
                        "order": 2,
                        "guide": "Pull-ups: 3 sets until failure",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1517343985841-f8b2d66e010b",
                        "youtube_link": "https://youtu.be/pullups"
                    },
                    {
                        "order": 3,
                        "guide": "Bent Over Rows: 3 sets of 12 reps",
                        "duration": 12,
                        "image": "https://images.unsplash.com/photo-1581009137042-c552e485697a",
                        "youtube_link": "https://youtu.be/bentoverrows"
                    },
                    {
                        "order": 4,
                        "guide": "Lat Pulldowns: 3 sets of 10 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1576678927484-cc907957088c",
                        "youtube_link": "https://youtu.be/latpulldowns"
                    },
                    {
                        "order": 5,
                        "guide": "Cool Down: 5 minutes stretching",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
                        "youtube_link": "https://youtu.be/cooldownback"
                    },
                ]
            },
            {
                "title": "Core Strengthening Routine",
                "description": "Build a strong core with targeted exercises for better stability and endurance.",
                "steps": [
                    {
                        "order": 1,
                        "guide": "Warm-up: 5 minutes light cardio",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1594737625785-a6cbdabd333c",
                        "youtube_link": "https://youtu.be/lightcardio"
                    },
                    {
                        "order": 2,
                        "guide": "Plank: 3 sets of 60 seconds",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1560347876-aeef00ee58a1",
                        "youtube_link": "https://youtu.be/plank"
                    },
                    {
                        "order": 3,
                        "guide": "Crunches: 3 sets of 20 reps",
                        "duration": 8,
                        "image": "https://images.unsplash.com/photo-1526401485004-6cfd9bf36f8e",
                        "youtube_link": "https://youtu.be/crunches"
                    },
                    {
                        "order": 4,
                        "guide": "Leg Raises: 3 sets of 15 reps",
                        "duration": 10,
                        "image": "https://images.unsplash.com/photo-1517638851339-4e76af50a6f3",
                        "youtube_link": "https://youtu.be/legraises"
                    },
                    {
                        "order": 5,
                        "guide": "Cool Down: 5 minutes stretching",
                        "duration": 5,
                        "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b",
                        "youtube_link": "https://youtu.be/corecooldown"
                    },
                ]
            },
        ]

        for data in workout_data:
            total_duration = sum(step["duration"] for step in data["steps"])
            wp = WorkoutPlan.objects.create(
                title=data["title"],
                description=data["description"],
                is_paid=random.choice([True, False]),
                thumbnail=random.choice(WORKOUT_THUMBNAILS),
                workout_duration=total_duration,
                youtube_link="https://youtu.be/workoutguide",
                steps=data["steps"],
                recommended_age_min=18,
                recommended_age_max=65,
                created_by=admin,
            )
            self.stdout.write(f"Created workout plan: {wp.title}")

        # -------------------------------
        # Seed 5 Meal Plans
        # -------------------------------
        meal_data = [
            {
                "title": "High Protein Power",
                "description": "A meal plan rich in protein to boost muscle recovery and growth.",
                "meal_type": "nonveg",
                "image": MEAL_IMAGES[0],
                "ingredients": [
                    {"name": "200g Chicken Breast", "alternative": "Tofu"},
                    {"name": "1 cup Quinoa", "alternative": ""},
                    {"name": "Broccoli", "alternative": "Spinach"},
                ],
                "directions": [
                    {"step": 1, "instruction": "Grill the chicken until fully cooked."},
                    {"step": 2, "instruction": "Cook quinoa according to package instructions."},
                    {"step": 3, "instruction": "Steam broccoli lightly."},
                ],
            },
            {
                "title": "Low Carb Delight",
                "description": "A meal plan designed to keep carbohydrates low while maintaining energy.",
                "meal_type": "nonveg",
                "image": MEAL_IMAGES[1],
                "ingredients": [
                    {"name": "Grilled Salmon", "alternative": ""},
                    {"name": "Mixed Green Salad", "alternative": ""},
                    {"name": "Avocado", "alternative": ""},
                ],
                "directions": [
                    {"step": 1, "instruction": "Grill salmon with your favorite herbs."},
                    {"step": 2, "instruction": "Toss greens with olive oil and lemon."},
                    {"step": 3, "instruction": "Slice avocado and serve on the side."},
                ],
            },
            {
                "title": "Vegan Vitality",
                "description": "A plant-based meal plan bursting with nutrients and vibrant flavors.",
                "meal_type": "veg",
                "image": MEAL_IMAGES[2],
                "ingredients": [
                    {"name": "Chickpeas", "alternative": ""},
                    {"name": "Sweet Potato", "alternative": ""},
                    {"name": "Kale", "alternative": "Spinach"},
                ],
                "directions": [
                    {"step": 1, "instruction": "Roast chickpeas with a blend of spices."},
                    {"step": 2, "instruction": "Bake sweet potato cubes until soft."},
                    {"step": 3, "instruction": "Toss kale with a light lemon dressing."},
                ],
            },
            {
                "title": "Paleo Perfection",
                "description": "A clean-eating meal plan inspired by Paleo principles.",
                "meal_type": "nonveg",
                "image": MEAL_IMAGES[3],
                "ingredients": [
                    {"name": "Grass-fed Beef", "alternative": ""},
                    {"name": "Cauliflower Rice", "alternative": ""},
                    {"name": "Asparagus", "alternative": ""},
                ],
                "directions": [
                    {"step": 1, "instruction": "Grill beef to your desired doneness."},
                    {"step": 2, "instruction": "Sauté cauliflower rice with garlic."},
                    {"step": 3, "instruction": "Steam asparagus until tender."},
                ],
            },
            {
                "title": "Balanced Nutrition",
                "description": "A well-rounded meal plan for overall health and sustained energy.",
                "meal_type": "nonveg",
                "image": MEAL_IMAGES[4],
                "ingredients": [
                    {"name": "Brown Rice", "alternative": ""},
                    {"name": "Mixed Vegetables", "alternative": ""},
                    {"name": "Fish Fillet", "alternative": "Paneer"},
                ],
                "directions": [
                    {"step": 1, "instruction": "Cook brown rice until fluffy."},
                    {"step": 2, "instruction": "Stir-fry mixed vegetables in olive oil."},
                    {"step": 3, "instruction": "Grill fish fillet or paneer as preferred."},
                ],
            },
        ]

        for data in meal_data:
            mp = MealPlan.objects.create(
                title=data["title"],
                description=data["description"],
                meal_type=data["meal_type"],
                image=data["image"],
                ingredients=data["ingredients"],
                directions=data["directions"],
                is_paid=random.choice([True, False]),
                created_by=admin
            )
            self.stdout.write(f"Created meal plan: {mp.title}")

        # -------------------------------
        # Seed 5 Success Stories
        # -------------------------------
        success_data = [
            {
                "title": "John's Incredible Transformation",
                "description": "John lost 40lbs and built impressive muscle through dedication and hard work.",
                "image": SUCCESS_IMAGES[0],
            },
            {
                "title": "Sarah's Marathon Journey",
                "description": "Sarah broke her own records by completing her first marathon with perseverance.",
                "image": SUCCESS_IMAGES[1],
            },
            {
                "title": "Mike's Muscle Milestone",
                "description": "Mike achieved his dream of gaining significant muscle mass with consistency.",
                "image": SUCCESS_IMAGES[2],
            },
            {
                "title": "Emma's Health Revival",
                "description": "Emma conquered chronic health issues and transformed her life with fitness.",
                "image": SUCCESS_IMAGES[3],
            },
            {
                "title": "Alex's Triumphant Triathlon",
                "description": "Alex pushed his limits and successfully completed a challenging triathlon.",
                "image": SUCCESS_IMAGES[4],
            },
        ]

        for data in success_data:
            story = SuccessStory.objects.create(
                title=data["title"],
                description=data["description"],
                image=data["image"],
            )
            self.stdout.write(f"Created success story: {story.title}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))
