"""Progress dashboard: charts and stats from WorkoutHistory + UserExerciseProgress."""

import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render

from ..models import UserExerciseProgress, WorkoutHistory


def _streak_days(dates: set) -> int:
    """Consecutive workout days ending today or yesterday."""
    if not dates:
        return 0
    cur = date.today()
    if cur not in dates:
        cur -= timedelta(days=1)
        if cur not in dates:
            return 0
    n = 0
    while cur in dates:
        n += 1
        cur -= timedelta(days=1)
    return n


@login_required
def progress_view(request):
    user = request.user
    history = WorkoutHistory.objects.filter(user=user)

    # headline stats
    total_workouts = history.count()
    totals = history.aggregate(minutes=Sum("duration_minutes"),
                               avg_difficulty=Avg("difficulty_rating"))
    workout_dates = {h.date() for h in
                     history.values_list("completed_at", flat=True)}
    week_start = date.today() - timedelta(days=date.today().weekday())
    this_week = sum(1 for d in workout_dates if d >= week_start)

    # last 8 weeks chart (workouts per week)
    weeks, week_counts = [], []
    for i in range(7, -1, -1):
        start = week_start - timedelta(weeks=i)
        end = start + timedelta(days=6)
        weeks.append(start.strftime("%b %d"))
        week_counts.append(sum(1 for d in workout_dates if start <= d <= end))

    # last 30 days activity strip
    days, day_flags = [], []
    for i in range(29, -1, -1):
        d = date.today() - timedelta(days=i)
        days.append(d.strftime("%d"))
        day_flags.append(1 if d in workout_dates else 0)

    # most-completed workout plans
    top_plans = (history.values("workout_plan__title")
                 .annotate(count=Count("id"))
                 .order_by("-count")[:5])

    # exercise personal bests
    top_exercises = (UserExerciseProgress.objects.filter(user=user)
                     .select_related("exercise")
                     .order_by("-times_completed")[:8])

    # recent sessions
    recent = history.select_related("workout_plan").order_by("-completed_at")[:10]

    context = {
        "total_workouts": total_workouts,
        "total_minutes": totals["minutes"] or 0,
        "avg_difficulty": round(totals["avg_difficulty"] or 0, 1),
        "this_week": this_week,
        "streak": _streak_days(workout_dates),
        "weeks_labels": json.dumps(weeks),
        "weeks_data": json.dumps(week_counts),
        "days_labels": json.dumps(days),
        "days_data": json.dumps(day_flags),
        "top_plans": list(top_plans),
        "top_exercises": top_exercises,
        "recent": recent,
    }
    return render(request, "progress.html", context)
