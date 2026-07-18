import uuid
import csv
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from ..models import (
    WorkoutPlan,
    MealPlan,
    Payment,
    SuccessStory,
    MealPlanReview,
    WorkoutPlanReview,
    WorkoutHistory,
)
from ..forms import WorkoutPlanReviewForm, MealPlanReviewForm
from django_esewa import EsewaPayment
from datetime import datetime, timedelta
from django.utils import timezone

# Import ML recommendation system (with fallback if dependencies not installed)
try:
    from ..ml_recommendations import get_user_recommendations, get_exercise_analytics
    ML_AVAILABLE = True
except ImportError as e:
    print(f"ML dependencies not available: {e}")
    ML_AVAILABLE = False
    
    def get_user_recommendations(user, num_recommendations=6):
        return {
            'exercise_recommendations': [],
            'workout_plan_recommendations': [],
            'questions': [],
            'user_profile_complete': False
        }
    
    def get_exercise_analytics():
        return {}

# Import local-LLM (Ollama) meal recommendations — no API key needed
try:
    from ..llm_recommendations import meal_recommendation_service
    GEMINI_AVAILABLE = True  # name kept for compatibility with checks below
except ImportError as e:
    print(f"Local AI not available: {e}")
    GEMINI_AVAILABLE = False


def home(request):
    workouts = WorkoutPlan.objects.order_by("-created_at")[:10]
    meals = MealPlan.objects.order_by("-created_at")[:10]
    recommended_workouts = []
    recommended_meals = []
    
    if request.user.is_authenticated:
        user = request.user
        
        # AI-powered meal recommendations using Gemini API
        if GEMINI_AVAILABLE and user.isProfileComplete:
            try:
                recommended_meals = meal_recommendation_service.get_recommended_meals(user, limit=4)
            except Exception as e:
                print(f"Error getting AI meal recommendations: {e}")
                recommended_meals = []
        
        # Fallback to basic recommendations if AI fails or profile incomplete
        if not recommended_meals:
            if user.subscription_type == "premium":
                if user.fitness_goal:
                    recommended_workouts_qs = WorkoutPlan.objects.filter(
                        description__icontains=user.fitness_goal)
                    if recommended_workouts_qs.count() < 2:
                        extra = WorkoutPlan.objects.order_by(
                            "?")[:(2 - recommended_workouts_qs.count())]
                        recommended_workouts = list(
                            recommended_workouts_qs) + list(extra)
                    else:
                        recommended_workouts = recommended_workouts_qs[:2]
                else:
                    recommended_workouts = WorkoutPlan.objects.order_by("?")[:2]
                
                if user.diet_preference == "veg":
                    rec_meals_qs = MealPlan.objects.filter(meal_type__iexact="veg")
                    if rec_meals_qs.count() < 2:
                        extra = MealPlan.objects.order_by(
                            "?")[:(2 - rec_meals_qs.count())]
                        recommended_meals = list(rec_meals_qs) + list(extra)
                    else:
                        recommended_meals = rec_meals_qs[:2]
                else:
                    recommended_meals = MealPlan.objects.order_by("?")[:2]
    
    context = {
        "workouts": workouts,
        "meals": meals,
        "recommended_workouts": recommended_workouts,
        "recommended_meals": recommended_meals,
        "ai_recommendations": GEMINI_AVAILABLE and request.user.is_authenticated and request.user.isProfileComplete,
    }
    return render(request, "home.html", context)


@login_required
def profile_view(request):
    # Get user's workout history with related workout plans
    workout_history = WorkoutHistory.objects.filter(
        user=request.user
    ).select_related('workout_plan').order_by('-completed_at')[:10]  # Get last 10 completions
    
    # Get workout statistics
    from django.db.models import Count
    total_workouts_completed = WorkoutHistory.objects.filter(user=request.user).count()
    unique_workouts_completed = WorkoutHistory.objects.filter(
        user=request.user
    ).values('workout_plan').distinct().count()
    
    # Get most frequent workouts
    favorite_workouts = WorkoutHistory.objects.filter(
        user=request.user
    ).values('workout_plan__title', 'workout_plan__id').annotate(
        completion_count=Count('id')
    ).order_by('-completion_count')[:5]
    
    context = {
        'user': request.user,
        'workout_history': workout_history,
        'total_workouts_completed': total_workouts_completed,
        'unique_workouts_completed': unique_workouts_completed,
        'favorite_workouts': favorite_workouts,
    }
    
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.phone = request.POST.get("phone", user.phone)
        user.bio = request.POST.get("bio", user.bio)
        user.gender = request.POST.get("gender", user.gender)
        age = request.POST.get("age", None)
        if age:
            try:
                user.age = int(age)
            except ValueError:
                user.age = None
        height = request.POST.get("height", None)
        if height:
            try:
                user.height = float(height)
            except ValueError:
                user.height = None
        weight = request.POST.get("weight", None)
        if weight:
            try:
                user.weight = float(weight)
            except ValueError:
                user.weight = None
        user.fitness_goal = request.POST.get("fitness_goal", user.fitness_goal)
        user.experience_level = request.POST.get(
            "experience_level", user.experience_level)
        workout_frequency = request.POST.get("workout_frequency", None)
        if workout_frequency:
            try:
                user.workout_frequency = int(workout_frequency)
            except ValueError:
                user.workout_frequency = None
        user.diet_preference = request.POST.get(
            "diet_preference", user.diet_preference)
        user.injuries = request.POST.get("injuries", user.injuries)
        if "profile_picture" in request.FILES:
            user.profile_picture = request.FILES["profile_picture"]
        try:
            user.save()
            messages.success(request, "Profile updated successfully!")
        except Exception as e:
            messages.error(
                request, "An error occurred while updating your profile.")
        return redirect("profile")
    return render(request, "edit_profile.html", {"user": user})


def workouts_list(request):
    query = request.GET.get("q", "")
    min_age = request.GET.get("min_age", "")
    max_age = request.GET.get("max_age", "")
    workouts_qs = WorkoutPlan.objects.all()
    if query:
        workouts_qs = workouts_qs.filter(
            Q(title__icontains=query) | Q(description__icontains=query))
    if min_age and max_age:
        try:
            min_age_val = int(min_age)
            max_age_val = int(max_age)
            workouts_qs = workouts_qs.filter(
                recommended_age_min__lte=min_age_val, recommended_age_max__gte=max_age_val)
        except ValueError:
            pass
    elif min_age:
        try:
            min_age_val = int(min_age)
            workouts_qs = workouts_qs.filter(
                recommended_age_min__lte=min_age_val)
        except ValueError:
            pass
    elif max_age:
        try:
            max_age_val = int(max_age)
            workouts_qs = workouts_qs.filter(
                recommended_age_max__gte=max_age_val)
        except ValueError:
            pass
    workouts_qs = workouts_qs.order_by("-created_at")
    paginator = Paginator(workouts_qs, 6)
    page_number = request.GET.get("page")
    workouts = paginator.get_page(page_number)
    paid_workout_ids = []
    if request.user.is_authenticated:
        paid_workout_ids = []
    
    # Check subscription status for premium content alerts
    has_valid_subscription = False
    subscription_expired = False
    if request.user.is_authenticated:
        has_valid_subscription = (
            request.user.subscription_type in ["basic", "premium"] and
            request.user.subscription_expiry and
            request.user.subscription_expiry > timezone.now()
        )
        subscription_expired = (
            request.user.subscription_expiry and
            request.user.subscription_expiry <= timezone.now()
        )
    
    context = {
        "query": query,
        "min_age": min_age,
        "max_age": max_age,
        "workouts": workouts,
        "paid_workout_ids": list(paid_workout_ids),
        "has_valid_subscription": has_valid_subscription,
        "subscription_expired": subscription_expired,
    }
    return render(request, "workouts.html", context)


def workout_detail(request, pk):
    from django.db.models import Avg, Count
    
    workout = get_object_or_404(WorkoutPlan, id=pk)

    # Allow access to free workouts without subscription check
    if not workout.is_paid:
        can_view_steps = True
    else:
        # Check subscription status for paid workouts
        if (not request.user.is_authenticated or
                request.user.subscription_type not in ["basic", "premium"] or
                not request.user.subscription_expiry or
                request.user.subscription_expiry <= timezone.now()):
            messages.error(
                request,
                "You do not have access to this page. Please login or upgrade your subscription."
            )
            return redirect('login') if not request.user.is_authenticated else redirect('purchase_subscription', plan='basic')
        can_view_steps = True

    steps = []
    if can_view_steps and workout.steps:
        steps = sorted(workout.steps, key=lambda x: x.get("order", 0))

    # Calculate average rating
    reviews_stats = workout.reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    avg_rating = reviews_stats['avg_rating'] or 0
    total_reviews = reviews_stats['total_reviews']

    # Get user's existing review if any
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = WorkoutPlanReview.objects.get(
                user=request.user, 
                workout_plan=workout
            )
        except WorkoutPlanReview.DoesNotExist:
            pass

    review_form = None
    if request.user.is_authenticated and not user_review:
        review_form = WorkoutPlanReviewForm()
        if request.method == "POST":
            review_form = WorkoutPlanReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.workout_plan = workout
                review.save()
                messages.success(request, "Review submitted successfully!")
                return redirect("workout_detail", pk=pk)

    # Get linked meal plans
    meal_plans = workout.linked_meal_plans.all()
    
    # Better workout recommendations based on user profile
    recommended_workouts_query = WorkoutPlan.objects.exclude(id=workout.id)
    
    if request.user.is_authenticated and hasattr(request.user, 'fitness_goal'):
        # If user has fitness goals, try to recommend similar workouts
        # This is a basic implementation - could be enhanced with ML recommendations
        if request.user.experience_level:
            recommended_workouts_query = recommended_workouts_query.filter(
                # Could add experience level to WorkoutPlan model in future
            )
    
    # Order by rating and limit results
    recommended_workouts = recommended_workouts_query.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('-avg_rating', '-review_count')[:6]

    context = {
        "workout": workout,
        "review_form": review_form,
        "can_view_steps": can_view_steps,
        "steps": steps,
        "meal_plans": meal_plans,
        "recommended_workouts": recommended_workouts,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "total_reviews": total_reviews,
        "user_review": user_review,
    }
    return render(request, "workout_detail.html", context)


@login_required
@require_POST
def complete_workout(request, pk):
    """Handle workout completion tracking"""
    workout = get_object_or_404(WorkoutPlan, id=pk)
    
    # Create workout history entry
    workout_history, created = WorkoutHistory.objects.get_or_create(
        user=request.user,
        workout_plan=workout,
        defaults={
            'completed_at': timezone.now()
        }
    )
    
    if created:
        # Optional: Get additional data from request
        duration = request.POST.get('duration_minutes')
        difficulty = request.POST.get('difficulty_rating')
        satisfaction = request.POST.get('satisfaction_rating')
        notes = request.POST.get('notes')
        
        if duration:
            try:
                workout_history.duration_minutes = int(duration)
            except ValueError:
                pass
                
        if difficulty:
            try:
                workout_history.difficulty_rating = int(difficulty)
            except ValueError:
                pass
                
        if satisfaction:
            try:
                workout_history.satisfaction_rating = int(satisfaction)
            except ValueError:
                pass
                
        if notes:
            workout_history.notes = notes
            
        workout_history.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Workout completed successfully! 🎉',
            'completed_at': workout_history.completed_at.strftime('%Y-%m-%d %H:%M')
        })
    else:
        # Update the completion time if already exists
        workout_history.completed_at = timezone.now()
        workout_history.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Workout completion updated! 🔄',
            'completed_at': workout_history.completed_at.strftime('%Y-%m-%d %H:%M')
        })


def meals_list(request):
    query = request.GET.get("q", "")
    ai_query = request.GET.get("ai_query", "")  # New AI query parameter
    
    if query.lower() in ['veg', 'nonveg']:
        meals_qs = MealPlan.objects.filter(meal_type=query.lower())
    elif query:
        meals_qs = MealPlan.objects.filter(title__icontains=query)
    else:
        meals_qs = MealPlan.objects.all()
    
    # Add pagination
    paginator = Paginator(meals_qs, 12)  # Show 12 meals per page
    page_number = request.GET.get('page')
    meals = paginator.get_page(page_number)
    
    # Get AI-powered meal recommendations - now available for all authenticated users
    recommended_meals = []
    ai_recommendations_available = False
    ai_response_message = ""
    
    if request.user.is_authenticated and GEMINI_AVAILABLE:
        ai_recommendations_available = True
        
        try:
            if ai_query:
                # Handle custom AI query
                print(f"Processing AI query: {ai_query}")
                recommended_meals = meal_recommendation_service.get_ai_query_recommendations(
                    request.user, ai_query, limit=6
                )
                ai_response_message = f"AI recommendations based on your query: '{ai_query}'"
            else:
                # Standard profile-based recommendations (works even with incomplete profile)
                recommended_meals = meal_recommendation_service.get_recommended_meals(request.user, limit=6)
                if request.user.isProfileComplete:
                    ai_response_message = "AI recommendations based on your complete profile"
                else:
                    ai_response_message = "AI recommendations based on available profile data (complete your profile for better recommendations)"
            
            print(f"Got {len(recommended_meals)} AI recommendations")
            
        except Exception as e:
            print(f"Error getting meal recommendations: {e}")
            recommended_meals = []
            ai_response_message = "Sorry, AI recommendations are temporarily unavailable"
    
    elif request.user.is_authenticated and not GEMINI_AVAILABLE:
        ai_response_message = "AI recommendations are not available"
    elif not request.user.is_authenticated:
        ai_response_message = "Please log in to get AI-powered meal recommendations"
    
    # Check subscription status for premium content alerts
    has_premium_subscription = False
    subscription_expired = False
    if request.user.is_authenticated:
        has_premium_subscription = (
            request.user.subscription_type == "premium" and
            request.user.subscription_expiry and
            request.user.subscription_expiry > timezone.now()
        )
        subscription_expired = (
            request.user.subscription_expiry and
            request.user.subscription_expiry <= timezone.now()
        )
    
    context = {
        "meals": meals, 
        "query": query,
        "ai_query": ai_query,
        "recommended_meals": recommended_meals,
        "ai_recommendations_available": ai_recommendations_available,
        "ai_response_message": ai_response_message,
        "has_premium_subscription": has_premium_subscription,
        "subscription_expired": subscription_expired,
    }
    return render(request, "meals.html", context)


def meal_detail(request, pk):
    meal = get_object_or_404(MealPlan, id=pk)
    if meal.is_paid:
        if not request.user.is_authenticated or request.user.subscription_type != "premium":
            messages.error(
                request,
                "This meal plan is exclusively available for premium subscribers. Please upgrade your subscription."
            )
            return redirect("pricing")
    existing_review = None
    if request.user.is_authenticated:
        existing_review = MealPlanReview.objects.filter(
            user=request.user, meal_plan=meal).first()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to submit a review.")
            return redirect("login")
        review_form = MealPlanReviewForm(
            request.POST, instance=existing_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.meal_plan = meal
            review.save()
            if existing_review:
                messages.success(request, "Review updated successfully!")
            else:
                messages.success(request, "Review submitted successfully!")
            return redirect("meal_detail", pk=pk)
    else:
        review_form = (
            MealPlanReviewForm(instance=existing_review)
            if request.user.is_authenticated
            else None
        )
    context = {
        "meal": meal,
        "review_form": review_form,
        "existing_review": existing_review,
    }
    return render(request, "meal_detail.html", context)


@require_POST
@login_required
def delete_meal_review(request, pk):
    meal = get_object_or_404(MealPlan, id=pk)
    if request.user.is_authenticated:
        review = MealPlanReview.objects.filter(
            user=request.user, meal_plan=meal).first()
        if review:
            review.delete()
            messages.success(request, "Review deleted successfully!")
    return redirect("meal_detail", pk=pk)


@require_POST
@login_required
def delete_review(request, pk):
    review = get_object_or_404(WorkoutPlanReview, id=pk)
    if review.user == request.user:
        review.delete()
        messages.success(request, "Review deleted successfully!")
    else:
        messages.error(
            request, "You are not authorized to delete this review.")
    return redirect("workout_detail", pk=review.workout_plan.id)


def success_list(request):
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    
    success_stories = SuccessStory.objects.all()
    
    # Filter by category if specified
    if category_filter:
        success_stories = success_stories.filter(category=category_filter)
    
    # Search functionality
    if search_query:
        success_stories = success_stories.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(motivation__icontains=search_query)
        )
    
    # Prioritize featured stories
    success_stories = success_stories.order_by('-is_featured', '-created_at')
    
    # Get category choices for filter dropdown
    categories = SuccessStory.TRANSFORMATION_CATEGORY_CHOICES
    
    context = {
        "success_stories": success_stories,
        "categories": categories,
        "selected_category": category_filter,
        "search_query": search_query,
    }
    return render(request, "success_list.html", context)


def success_detail(request, pk):
    story = get_object_or_404(SuccessStory, pk=pk)
    
    # Get related success stories (same category or random)
    related_stories = SuccessStory.objects.filter(category=story.category).exclude(pk=pk)[:3]
    if related_stories.count() < 3:
        additional_stories = SuccessStory.objects.exclude(pk=pk).exclude(
            pk__in=[s.pk for s in related_stories]
        ).order_by('?')[:3-related_stories.count()]
        related_stories = list(related_stories) + list(additional_stories)
    
    context = {
        "story": story,
        "related_stories": related_stories,
    }
    return render(request, "success_detail.html", context)


@login_required(login_url="/login")
def pricing(request):
    context = {}
    if request.user.is_authenticated:
        if (
            request.user.subscription_expiry
            and request.user.subscription_expiry > timezone.now()
            and request.user.subscription_type in ["basic", "premium"]
        ):
            context["active_subscription"] = True
            context["subscription_expiry"] = request.user.subscription_expiry
        else:
            context["active_subscription"] = False
    return render(request, "pricing.html", context)


@login_required
def purchase_subscription(request, plan):
    if plan not in ["basic", "premium"]:
        messages.error(request, "Invalid subscription plan selected.")
        return redirect("pricing")

    price = 200 if plan == "basic" else 500

    transaction_uuid = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=request.user,
        amount=price,
        transaction_id=transaction_uuid,
        status="pending",  # This field exists on your Payment model.
    )

    esewa_payment = EsewaPayment()
    
    # Set all required eSewa parameters
    esewa_payment.amount = float(price)
    esewa_payment.tax_amount = 0.0
    esewa_payment.total_amount = float(price)
    esewa_payment.transaction_uuid = transaction_uuid
    esewa_payment.product_code = "EPAYTEST"  # Use product_code instead of merchant_code
    esewa_payment.product_service_charge = 0.0
    esewa_payment.product_delivery_charge = 0.0

    success_url = request.build_absolute_uri(
        f"/payment/subscription/success/?transaction_id={transaction_uuid}&amount={price}&plan={plan}"
    )
    failure_url = request.build_absolute_uri("/payment/subscription/failure/")
    esewa_payment.success_url = success_url
    esewa_payment.failure_url = failure_url
    
    # Create signature
    esewa_payment.create_signature()

    esewa_form = esewa_payment.generate_form()

    context = {
        "plan": plan,
        "price": price,
        "esewa_form": esewa_form,
        "transaction_uuid": transaction_uuid,
    }
    return render(request, "purchase_subscription.html", context)


@login_required
def payment_success_subscription(request):
    transaction_uuid = request.GET.get("transaction_id")
    amount_str = request.GET.get("amount")
    plan = request.GET.get("plan")

    if plan and "?" in plan:
        plan = plan.split("?")[0]

    if not amount_str:
        messages.error(request, "Invalid payment data.")
        return redirect("pricing")

    try:
        amount = float(amount_str.split("?")[0])
    except Exception:
        messages.error(request, "Invalid amount received.")
        return redirect("pricing")


    try:
        payment = Payment.objects.get(transaction_id=transaction_uuid)
        payment.status = "completed"
        payment.save()
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect("pricing")

    request.user.subscription_type = plan
    request.user.subscription_expiry = timezone.now() + timedelta(days=30)
    request.user.save()

    messages.success(
        request,
        "Payment successful! Your subscription has been updated and is valid for 1 month."
    )
    return redirect("profile")


def payment_failure_subscription(request):
    messages.error(request, "Payment failed. Please try again.")
    return redirect("pricing")


@login_required(login_url="/login")
def ai_exercises(request):
    """
    AI Exercise Database view - displays gym dataset with search functionality
    and personalized recommendations
    """
    # Get user recommendations if logged in
    user_recommendations = None
    if request.user.is_authenticated:
        try:
            user_recommendations = get_user_recommendations(request.user, 6)
        except Exception as e:
            messages.info(request, "Recommendations temporarily unavailable.")
            user_recommendations = {
                'exercise_recommendations': [],
                'workout_plan_recommendations': [],
                'questions': [],
                'user_profile_complete': False
            }
    
    # Get the CSV file path
    csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'megaGymDataset.csv')
    
    exercises = []
    search_query = request.GET.get('search', '').strip()
    equipment_filter = request.GET.get('equipment', '').strip()
    body_part_filter = request.GET.get('body_part', '').strip()
    level_filter = request.GET.get('level', '').strip()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Convert rating to float if present, otherwise set to 0
                try:
                    rating = float(row.get('Rating', 0)) if row.get('Rating') else 0.0
                except ValueError:
                    rating = 0.0
                
                exercise = {
                    'title': row.get('Title', ''),
                    'description': row.get('Desc', ''),
                    'type': row.get('Type', ''),
                    'body_part': row.get('BodyPart', ''),
                    'equipment': row.get('Equipment', ''),
                    'level': row.get('Level', ''),
                    'rating': rating,
                    'rating_desc': row.get('RatingDesc', '')
                }
                
                # Apply filters
                if search_query:
                    if (search_query.lower() not in exercise['title'].lower() and 
                        search_query.lower() not in exercise['description'].lower() and
                        search_query.lower() not in exercise['body_part'].lower()):
                        continue
                
                if equipment_filter and equipment_filter.lower() != exercise['equipment'].lower():
                    continue
                    
                if body_part_filter and body_part_filter.lower() != exercise['body_part'].lower():
                    continue
                    
                if level_filter and level_filter.lower() != exercise['level'].lower():
                    continue
                
                exercises.append(exercise)
    
    except FileNotFoundError:
        messages.error(request, "Exercise database file not found.")
    except Exception as e:
        messages.error(request, f"Error loading exercise database: {str(e)}")
    
    # Get unique values for filter dropdowns
    unique_equipment = set()
    unique_body_parts = set()
    unique_levels = set()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row.get('Equipment'):
                    unique_equipment.add(row['Equipment'])
                if row.get('BodyPart'):
                    unique_body_parts.add(row['BodyPart'])
                if row.get('Level'):
                    unique_levels.add(row['Level'])
    except:
        pass
    
    # Pagination
    paginator = Paginator(exercises, 20)  # Show 20 exercises per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get exercise analytics
    try:
        analytics = get_exercise_analytics()
    except:
        analytics = {}
    
    context = {
        'exercises': page_obj,
        'search_query': search_query,
        'equipment_filter': equipment_filter,
        'body_part_filter': body_part_filter,
        'level_filter': level_filter,
        'unique_equipment': sorted(unique_equipment),
        'unique_body_parts': sorted(unique_body_parts),
        'unique_levels': sorted(unique_levels),
        'total_exercises': len(exercises),
        'user_recommendations': user_recommendations,
        'analytics': analytics,
        'ml_available': ML_AVAILABLE
    }
    
    return render(request, 'ai_exercises.html', context)


@login_required
def update_user_preferences(request):
    """
    AJAX endpoint to update user preferences for better recommendations
    """
    if request.method == 'POST':
        user = request.user
        
        # Update user preferences based on form data
        fitness_goal = request.POST.get('fitness_goal')
        experience_level = request.POST.get('experience_level')
        workout_frequency = request.POST.get('workout_frequency')
        equipment_preference = request.POST.get('equipment_preference')
        workout_duration = request.POST.get('workout_duration')
        body_focus = request.POST.get('body_focus')
        
        updated_fields = []
        
        if fitness_goal and fitness_goal != user.fitness_goal:
            user.fitness_goal = fitness_goal
            updated_fields.append('fitness_goal')
        
        if experience_level and experience_level != user.experience_level:
            user.experience_level = experience_level
            updated_fields.append('experience_level')
        
        if workout_frequency:
            try:
                freq_num = int(workout_frequency.split('-')[0])
                user.workout_frequency = freq_num
                updated_fields.append('workout_frequency')
            except:
                pass
        
        user.save()
        
        # Generate new recommendations
        try:
            recommendations = get_user_recommendations(user, 6)
            return JsonResponse({
                'success': True,
                'message': f'Updated {len(updated_fields)} preferences',
                'recommendations': recommendations
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating recommendations: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def get_meal_recommendations_ajax(request):
    """AJAX endpoint to get fresh meal recommendations"""
    if not GEMINI_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'AI recommendations not available'})
    
    if not request.user.isProfileComplete:
        return JsonResponse({'success': False, 'error': 'Profile not complete'})
    
    try:
        recommended_meals = meal_recommendation_service.get_recommended_meals(request.user, limit=6)
        
        # Convert meal objects to JSON serializable format
        meals_data = []
        for meal in recommended_meals:
            meals_data.append({
                'id': meal.id,
                'title': meal.title,
                'description': meal.description,
                'meal_type': meal.get_meal_type_display(),
                'is_paid': meal.is_paid,
                'image_url': meal.image.url if meal.image else None,
                'relevance_score': getattr(meal, 'relevance_score', 0.0),
                'recommendation_reason': getattr(meal, 'recommendation_reason', ''),
            })
        
        return JsonResponse({
            'success': True,
            'meals': meals_data
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
