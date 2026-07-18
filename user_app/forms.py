from django import forms
from .models import WorkoutPlanReview, MealPlanReview


class WorkoutPlanReviewForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlanReview
        fields = ["rating", "review"]
        widgets = {
            "rating": forms.NumberInput(attrs={
                "class": (
                    "w-full px-4 py-2 border border-gray-300 rounded-md "
                    "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                ),
                "placeholder": "Enter your rating (1-5)"
            }),
            "review": forms.Textarea(attrs={
                "class": (
                    "w-full px-4 py-2 border border-gray-300 rounded-md "
                    "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                ),
                "placeholder": "Share your feedback...",
                "rows": "4",
            })
        }


class MealPlanReviewForm(forms.ModelForm):
    class Meta:
        model = MealPlanReview  # accesses the django model MealPlanReview
        fields = ["rating", "review"]
        widgets = {
            "rating": forms.NumberInput(attrs={
                "class": (
                    "w-full px-4 py-2 border border-gray-300 rounded-md "
                    "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                ),
                "placeholder": "Enter your rating (1-5)"
            }),
            "review": forms.Textarea(attrs={
                "class": (
                    "w-full px-4 py-2 border border-gray-300 rounded-md "
                    "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                ),
                "placeholder": "Write your review here...",
                "rows": "4",
            })
        }
