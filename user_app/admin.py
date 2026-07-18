import json
from django import forms
from django.contrib import admin
from django.db import models
from .models import (
    CustomUser,
    EmailVerification,
    WorkoutPlan,
    MealPlan,
    WorkoutPlanReview,
    MealPlanReview,
    SuccessStory,
)

class StepsEditorWidget(forms.Widget):
    template_name = 'admin/steps_editor_widget.html'

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
        )
        css = {
            'all': ()
        }

    def format_value(self, value):
        if value is None:
            return '[]'
        if isinstance(value, list):
            return json.dumps(value)
        return value

    def get_context(self, name, value, attrs):
        if value is None:
            value = '[]'
        context = super().get_context(name, value, attrs)
        try:
            steps = json.loads(value)
        except Exception:
            steps = []
        context['widget']['steps'] = steps
        context['widget']['name'] = name
        context['widget']['value'] = value
        return context


class IngredientsEditorWidget(forms.Widget):
    template_name = 'admin/ingredients_editor_widget.html'

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
        )
        css = {
            'all': ()
        }

    def format_value(self, value):
        if value is None:
            return '[]'
        if isinstance(value, list):
            return json.dumps(value)
        return value

    def get_context(self, name, value, attrs):
        if value is None:
            value = '[]'
        context = super().get_context(name, value, attrs)
        try:
            ingredients = json.loads(value)
        except Exception:
            ingredients = []
        context['widget']['ingredients'] = ingredients
        context['widget']['name'] = name
        context['widget']['value'] = value
        return context


class DirectionsEditorWidget(forms.Widget):
    template_name = 'admin/directions_editor_widget.html'

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
        )
        css = {
            'all': ()
        }

    def format_value(self, value):
        if value is None:
            return '[]'
        if isinstance(value, list):
            return json.dumps(value)
        return value

    def get_context(self, name, value, attrs):
        if value is None:
            value = '[]'
        context = super().get_context(name, value, attrs)
        try:
            directions = json.loads(value)
        except Exception:
            directions = []
        context['widget']['directions'] = directions
        context['widget']['name'] = name
        context['widget']['value'] = value
        return context


class WorkoutPlanReviewInline(admin.TabularInline):
    model = WorkoutPlanReview
    extra = 1


class MealPlanReviewInline(admin.TabularInline):
    model = MealPlanReview
    extra = 1


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "username", "email", "is_staff", "is_superuser", "is_active"
    )
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("email",)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verified", "created_at")
    search_fields = ("user__email",)
    ordering = ("-created_at",)


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = (
        "title", "created_by", "is_paid", "workout_duration", "created_at"
    )
    search_fields = ("title", "description", "created_by__email")
    list_filter = ("is_paid",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [WorkoutPlanReviewInline]
    fieldsets = (
        (None, {
            "fields": (
                "title", "description", "created_by", "is_paid",
                "thumbnail", "workout_duration", "youtube_link", "steps"
            )
        }),
        ("Additional Options", {
            "classes": ("collapse",),
            "fields": (
                "linked_meal_plans", "recommended_age_min", "recommended_age_max"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )
    formfield_overrides = {
        models.JSONField: {"widget": StepsEditorWidget()},
    }


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = (
        "title", "created_by", "is_paid", "meal_type", "created_at"
    )
    search_fields = ("title", "description", "created_by__email")
    list_filter = ("is_paid", "meal_type")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [MealPlanReviewInline]
    fieldsets = (
        (None, {
            "fields": (
                "title", "description", "created_by", "is_paid", "meal_type",
                "image", "ingredients", "directions"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "ingredients":
            kwargs["widget"] = IngredientsEditorWidget()
        elif db_field.name == "directions":
            kwargs["widget"] = DirectionsEditorWidget()
        return super().formfield_for_dbfield(db_field, **kwargs)


@admin.register(WorkoutPlanReview)
class WorkoutPlanReviewAdmin(admin.ModelAdmin):
    list_display = (
        "workout_plan", "user", "rating", "created_at"
    )
    search_fields = (
        "workout_plan__title", "user__email", "review"
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(MealPlanReview)
class MealPlanReviewAdmin(admin.ModelAdmin):
    list_display = (
        "meal_plan", "user", "rating", "created_at"
    )
    search_fields = (
        "meal_plan__title", "user__email", "review"
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = (
        "title", 
        "category", 
        "user", 
        "duration", 
        "is_featured", 
        "is_verified", 
        "created_at"
    )
    list_filter = (
        "category", 
        "is_featured", 
        "is_verified", 
        "created_at"
    )
    search_fields = (
        "title", 
        "description", 
        "motivation", 
        "user__email", 
        "user__first_name", 
        "user__last_name"
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "title",
                "description", 
                "user",
                "category",
                "is_featured",
                "is_verified"
            )
        }),
        ("Images", {
            "fields": (
                "image",
                "before_image", 
                "after_image"
            )
        }),
        ("Transformation Details", {
            "fields": (
                "duration",
                "starting_weight",
                "current_weight", 
                "weight_loss",
                "biggest_achievement"
            )
        }),
        ("Journey Details", {
            "fields": (
                "motivation",
                "key_challenges",
                "workout_routine",
                "diet_changes",
                "advice_for_others"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        })
    )
    
    actions = ["mark_as_featured", "mark_as_verified", "unmark_as_featured", "unmark_as_verified"]
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} stories marked as featured.")
    mark_as_featured.short_description = "Mark selected stories as featured"
    
    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} stories marked as verified.")
    mark_as_verified.short_description = "Mark selected stories as verified"
    
    def unmark_as_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} stories unmarked as featured.")
    unmark_as_featured.short_description = "Unmark selected stories as featured"
    
    def unmark_as_verified(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f"{queryset.count()} stories unmarked as verified.")
    unmark_as_verified.short_description = "Unmark selected stories as verified"



