from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    groups = models.ManyToManyField(
        Group,
        related_name="custom_users",
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_users",
        blank=True,
        help_text="Specific permissions for this user.",
    )
    isProfileComplete = models.BooleanField(default=False)
    height = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    FITNESS_GOAL_CHOICES = [
        ("weight_loss", "Weight Loss"),
        ("muscle_gain", "Muscle Gain"),
        ("endurance", "Endurance"),
        ("flexibility", "Flexibility"),
        ("general_health", "General Health"),
    ]
    fitness_goal = models.CharField(
        max_length=20, choices=FITNESS_GOAL_CHOICES, blank=True, null=True
    )
    EXPERIENCE_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    experience_level = models.CharField(
        max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, blank=True, null=True
    )
    workout_frequency = models.PositiveIntegerField(blank=True, null=True)
    DIET_PREFERENCE_CHOICES = [
        ("veg", "Vegetarian"),
        ("non_veg", "Non-Vegetarian"),
    ]
    diet_preference = models.CharField(
        max_length=20, choices=DIET_PREFERENCE_CHOICES, blank=True, null=True
    )
    injuries = models.TextField(blank=True, null=True)
    SUBSCRIPTION_CHOICES = [("basic", "Basic"), ("premium", "Premium"),
                            ("none", "None")]
    subscription_type = models.CharField(
        max_length=10, choices=SUBSCRIPTION_CHOICES, default="none"
    )
    subscription_expiry = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "email"  # Use username as email
    # Here 'username' is still required for compatibility
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class EmailVerification(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="email_verification"
    )
    bio = models.TextField(blank=True)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.user.email}"


class WorkoutPlan(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workout_plans",
    )
    is_paid = models.BooleanField(default=False)
    thumbnail = models.ImageField(
        upload_to="workout_thumbnails/", blank=True, null=True
    )
    linked_meal_plans = models.ManyToManyField(
        "MealPlan", blank=True, related_name="workout_plans"
    )
    workout_duration = models.PositiveIntegerField(default=30)
    youtube_link = models.URLField(blank=True, null=True)
    recommended_age_min = models.PositiveIntegerField(default=15)
    recommended_age_max = models.PositiveIntegerField(default=60)
    steps = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "List of steps for the workout. Format: "
            '[{"order": number, "guide": "instruction", "duration": minutes, '
            '"image": "URL", "youtube_link": "URL"}, ...]'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class MealPlan(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="meal_plans",
    )
    is_paid = models.BooleanField(default=False)
    MEAL_TYPE_CHOICES = [("veg", "Vegetarian"), ("nonveg", "Non-Vegetarian")]
    meal_type = models.CharField(
        max_length=10, choices=MEAL_TYPE_CHOICES, blank=True, null=True
    )
    image = models.ImageField(
        upload_to="meal_images/", blank=True, null=True
    )
    ingredients = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "List of ingredients. Format: "
            "[{'name': '15 almonds', 'alternative': 'hazelnuts'}, ...]"
        ),
    )
    directions = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "List of directions. Format: "
            "[{'step': 1, 'instruction': 'Wash the apple'}, ...]"
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg) if avg else 0


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.status}"


class WorkoutPlanReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_reviews",
    )
    workout_plan = models.ForeignKey(
        WorkoutPlan, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.email} for {self.workout_plan.title}"


class MealPlanReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meal_reviews",
    )
    meal_plan = models.ForeignKey(
        MealPlan, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.email} for {self.meal_plan.title}"


class SuccessStory(models.Model):
    TRANSFORMATION_CATEGORY_CHOICES = [
        ("weight_loss", "Weight Loss"),
        ("muscle_gain", "Muscle Gain"),
        ("fitness_journey", "Fitness Journey"),
        ("lifestyle_change", "Lifestyle Change"),
        ("health_recovery", "Health Recovery"),
        ("strength_building", "Strength Building"),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="success_stories",
    )
    category = models.CharField(
        max_length=20,
        choices=TRANSFORMATION_CATEGORY_CHOICES,
        default="fitness_journey"
    )
    image = models.ImageField(
        upload_to="success_stories/", blank=True, null=True
    )
    before_image = models.ImageField(
        upload_to="success_stories/before/", blank=True, null=True
    )
    after_image = models.ImageField(
        upload_to="success_stories/after/", blank=True, null=True
    )
    duration = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="e.g., '6 months', '1 year', '18 weeks'"
    )
    weight_loss = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., '25 lbs', '15 kg', 'No weight focus'"
    )
    starting_weight = models.FloatField(blank=True, null=True, help_text="in kg")
    current_weight = models.FloatField(blank=True, null=True, help_text="in kg")
    motivation = models.TextField(
        blank=True,
        null=True,
        help_text="What motivated this transformation"
    )
    key_challenges = models.TextField(
        blank=True,
        null=True,
        help_text="Main challenges faced during the journey"
    )
    workout_routine = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of workout routine followed"
    )
    diet_changes = models.TextField(
        blank=True,
        null=True,
        help_text="Key dietary changes made"
    )
    biggest_achievement = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Single biggest achievement or milestone"
    )
    advice_for_others = models.TextField(
        blank=True,
        null=True,
        help_text="Advice for others starting their fitness journey"
    )
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Success Stories"

    def __str__(self):
        return self.title

    def get_weight_loss_display(self):
        """Calculate and display weight loss if start and current weight are available"""
        if self.starting_weight and self.current_weight:
            loss = self.starting_weight - self.current_weight
            return f"{loss:.1f} kg" if loss > 0 else "Weight maintained"
        return self.weight_loss or "Not specified"


class Exercise(models.Model):
    """
    Model to store exercise data from the CSV dataset for better performance
    """
    EXERCISE_TYPE_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('plyometrics', 'Plyometrics'),
        ('powerlifting', 'Powerlifting'),
        ('stretching', 'Stretching'),
    ]
    
    DIFFICULTY_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    exercise_type = models.CharField(
        max_length=50, 
        choices=EXERCISE_TYPE_CHOICES, 
        blank=True, 
        null=True,
        db_index=True
    )
    body_part = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    equipment = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    difficulty_level = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_LEVEL_CHOICES, 
        blank=True, 
        null=True,
        db_index=True
    )
    rating = models.FloatField(default=0.0, db_index=True)
    rating_description = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional fields for better recommendations
    is_compound = models.BooleanField(default=False, help_text="Is this a compound movement?")
    is_unilateral = models.BooleanField(default=False, help_text="Is this a unilateral exercise?")
    requires_spotter = models.BooleanField(default=False)
    estimated_calories_per_minute = models.FloatField(default=0.0)
    
    # Search and recommendation fields
    tags = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Tags for better search and recommendations"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rating', 'title']
        indexes = [
            models.Index(fields=['body_part', 'difficulty_level']),
            models.Index(fields=['equipment', 'exercise_type']),
            models.Index(fields=['rating', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_difficulty_color(self):
        """Return CSS color class for difficulty level"""
        colors = {
            'beginner': 'text-green-400',
            'intermediate': 'text-yellow-400',
            'advanced': 'text-red-400'
        }
        return colors.get(self.difficulty_level, 'text-gray-400')


class UserExerciseProgress(models.Model):
    """
    Track user progress with specific exercises
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exercise_progress"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    
    # Progress tracking
    times_completed = models.PositiveIntegerField(default=0)
    last_completed = models.DateTimeField(blank=True, null=True)
    personal_best_weight = models.FloatField(blank=True, null=True)
    personal_best_reps = models.PositiveIntegerField(blank=True, null=True)
    personal_best_time = models.DurationField(blank=True, null=True)
    
    # User feedback
    difficulty_rating = models.PositiveSmallIntegerField(
        blank=True, 
        null=True,
        help_text="User's perceived difficulty (1-5)"
    )
    enjoyment_rating = models.PositiveSmallIntegerField(
    blank=True, 
        null=True,
        help_text="How much user enjoys this exercise (1-5)"
    )
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'exercise']
        ordering = ['-last_completed', '-times_completed']

    def __str__(self):
        return f"{self.user.username} - {self.exercise.title}"


class WorkoutHistory(models.Model):
    """
    Track when users complete workouts
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_history"
    )
    workout_plan = models.ForeignKey(
        WorkoutPlan, 
        on_delete=models.CASCADE,
        related_name="completion_history"
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Track performance metrics
    duration_minutes = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="How long the workout took in minutes"
    )
    difficulty_rating = models.PositiveSmallIntegerField(
        blank=True, 
        null=True,
        help_text="User's perceived difficulty (1-5)"
    )
    satisfaction_rating = models.PositiveSmallIntegerField(
        blank=True, 
        null=True,
        help_text="How satisfied user was with the workout (1-5)"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="User's notes about the workout session"
    )
    
    class Meta:
        ordering = ['-completed_at']
        verbose_name_plural = "Workout History"

    def __str__(self):
        return f"{self.user.username} completed {self.workout_plan.title} on {self.completed_at.strftime('%Y-%m-%d')}"


class PersonalWorkoutPlan(models.Model):
    """
    A custom workout plan generated by the AI Coach for a specific user.
    `days` structure: [{"day": "Day 1", "focus": "Chest & Triceps",
        "exercises": [{"name": str, "sets": int, "reps": str,
                       "duration_min": int, "notes": str}]}]
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_plans",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=50, blank=True)
    days = models.JSONField(default=list)
    is_active = models.BooleanField(default=False,
                                    help_text="The plan the user is currently following")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"
