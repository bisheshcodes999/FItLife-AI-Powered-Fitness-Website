from django.urls import path
from .views import login,logout,register,verify,home,workout_detail,workouts_list,profile_complete,meal_detail,meals_list,success_list,success_detail,profile_view,edit_profile,delete_meal_review,delete_review,pricing,payment_failure_subscription,payment_success_subscription,purchase_subscription,ai_exercises,update_user_preferences,get_meal_recommendations_ajax,complete_workout,progress_view,coach_view,coach_chat_api,my_plans,plan_detail,plan_delete,plan_activate
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("",home,name="home"),
    path("pricing/", pricing, name="pricing"),
    path(
        "purchase-subscription/<str:plan>/",
        purchase_subscription,
        name="purchase_subscription",
    ),
    path(
        "payment/subscription/success/",
        payment_success_subscription,
        name="payment_success_subscription",
    ),
    path(
        "payment/subscription/failure/",
        payment_failure_subscription,
        name="payment_failure_subscription",
    ),
    path("login/", login, name="login"),
    path("register/", register, name="register"),
    path("logout/", logout, name="logout"),
    path("verify/", verify, name="verify"),
    path("workouts/", workouts_list, name="workouts_list"),
    path("workout/<int:pk>/", workout_detail, name="workout_detail"),
    path("workout/<int:pk>/complete/", complete_workout, name="complete_workout"),
    path(
        "workouts/review/delete/<int:pk>/",
        delete_review,
        name="delete_review"
    ),
    path("meals/", meals_list, name="meals_list"),
    path("meal/<int:pk>/", meal_detail, name="meal_detail"),
    path("meal/<int:pk>/delete-review/", delete_meal_review, name="delete_meal_review"),
    path("success-stories/", success_list, name="success_stories"),
    path("success-stories/<int:pk>/", success_detail, name="success_detail"),
    path("profile/", profile_view, name="profile"),
    path("edit-profile/", edit_profile, name="edit_profile"),
    path("ai/", ai_exercises, name="ai_exercises"),
    path("progress/", progress_view, name="progress"),
    path("coach/", coach_view, name="coach"),
    path("api/coach-chat/", coach_chat_api, name="coach_chat"),
    path("my-plans/", my_plans, name="my_plans"),
    path("my-plans/<int:pk>/", plan_detail, name="plan_detail"),
    path("my-plans/<int:pk>/delete/", plan_delete, name="plan_delete"),
    path("my-plans/<int:pk>/activate/", plan_activate, name="plan_activate"),
    path("api/update-preferences/", update_user_preferences, name="update_user_preferences"),
    path("api/meal-recommendations/", get_meal_recommendations_ajax, name="get_meal_recommendations_ajax"),

    

     # Password Reset Request – the user submits their email here.
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"),
        name="password_reset",
    ),
    # Inform the user that an email has been sent.
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"),
        name="password_reset_done",
    ),
    # The link from the email goes here, with uid and token for verification.
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    # Final confirmation that the password has been reset.
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path('profile-complete/',profile_complete,name='profile_complete'),
]
