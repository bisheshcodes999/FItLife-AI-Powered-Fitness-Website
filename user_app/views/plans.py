"""My Plans — AI-generated personal workout plans."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import PersonalWorkoutPlan


@login_required
def my_plans(request):
    plans = PersonalWorkoutPlan.objects.filter(user=request.user)
    return render(request, "my_plans.html", {"plans": plans})


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(PersonalWorkoutPlan, pk=pk, user=request.user)
    return render(request, "plan_detail.html", {"plan": plan})


@login_required
@require_POST
def plan_delete(request, pk):
    plan = get_object_or_404(PersonalWorkoutPlan, pk=pk, user=request.user)
    plan.delete()
    messages.success(request, "Plan deleted.")
    return redirect("my_plans")


@login_required
@require_POST
def plan_activate(request, pk):
    plan = get_object_or_404(PersonalWorkoutPlan, pk=pk, user=request.user)
    PersonalWorkoutPlan.objects.filter(user=request.user).update(is_active=False)
    plan.is_active = True
    plan.save()
    messages.success(request, f"'{plan.title}' is now your active plan!")
    return redirect("plan_detail", pk=pk)
