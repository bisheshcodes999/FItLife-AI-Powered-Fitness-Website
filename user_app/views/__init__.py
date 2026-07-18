from .view import home,workouts_list,workout_detail,meals_list,meal_detail,success_list,success_detail,profile_view,edit_profile,delete_meal_review,delete_review,pricing,purchase_subscription,payment_success_subscription,payment_failure_subscription,ai_exercises,update_user_preferences,get_meal_recommendations_ajax,complete_workout
from .auth import login, register, logout, verify,profile_complete
from .progress import progress_view
from .coach import coach_view, coach_chat_api
from .plans import my_plans, plan_detail, plan_delete, plan_activate

__all__ = [
    'home',
    'login',
    'register',
    'logout',
    'verify',
    'workout',
    'porfile_complete',
    'workouts_list',
    'workout_detail',
    'meals_list',
    'meal_detail',
    'success_list',
    'success_detail',
    'profile_view',
    'edit_profile',
    'delete_meal_review',
    'delete_review',
    'pricing',
    'purchase_subscription',
    'payment_success_subscription',
    'payment_failure_subscription',
    'ai_exercises',
    'update_user_preferences',
    'get_meal_recommendations_ajax',
    'complete_workout',
    'progress_view',
    'coach_view',
    'coach_chat_api',
    'my_plans',
    'plan_detail',
    'plan_delete',
    'plan_activate',
]