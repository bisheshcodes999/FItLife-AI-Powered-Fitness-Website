"""FitLife AI Coach — local Ollama agent with tools over the app's real data.

The bot can search workouts/meals in the database, read the user's progress,
and answer fitness questions personalized to their profile.
"""

import json
import os
import urllib.request
from datetime import date, timedelta

from django.db.models import Count, Q, Sum

from .models import MealPlan, PersonalWorkoutPlan, WorkoutHistory, WorkoutPlan

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").strip().rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b").strip()

SYSTEM_TEMPLATE = """You are FitLife Coach, the AI assistant inside the FitLife
fitness app. You help with workouts, training advice, and meals.

User profile:
{profile}

Rules:
- Use the tools to ground answers in the app's REAL workout plans, meal plans
  and the user's actual progress — don't invent plans that aren't in the app.
- When the user asks you to CREATE/MAKE/PREPARE a workout plan for them
  (e.g. "make me a plan", "create a 4-day split"), design a complete plan
  tailored to their profile, goal, level, frequency and injuries, then SAVE it
  with the create_workout_plan tool. Ask a clarifying question first ONLY if
  you don't know how many days/week they want. After saving, summarize the
  plan briefly and tell them it's saved in "My Plans".
- When recommending a plan or meal from the database, mention its exact title
  so the user can find it.
- Respect the user's fitness goal, experience level, diet preference and
  injuries. Never suggest exercises that conflict with stated injuries.
- Be motivating, specific and concise. No medical diagnoses — suggest a
  professional for pain/injury concerns.
- Do not show internal reasoning; reply with the final answer only."""

TOOLS = [
    {"type": "function", "function": {
        "name": "search_workouts",
        "description": "Search the app's workout plan database by keyword "
                       "(e.g. 'cardio', 'beginner strength', 'hiit').",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "search_meals",
        "description": "Search the app's meal plan database by keyword.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_my_progress",
        "description": "Get the user's workout stats: totals, streak, "
                       "this week, favourite plans, recent sessions.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "create_workout_plan",
        "description": "Save a personalized workout plan you designed for the "
                       "user. Call this AFTER designing the full plan.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "e.g. '4-Day Muscle Gain Split'"},
            "description": {"type": "string", "description": "1-2 sentence overview"},
            "goal": {"type": "string", "description": "e.g. muscle_gain"},
            "days": {"type": "array", "description": "One entry per training day",
                "items": {"type": "object", "properties": {
                    "day": {"type": "string", "description": "e.g. 'Day 1 - Monday'"},
                    "focus": {"type": "string", "description": "e.g. 'Chest & Triceps'"},
                    "exercises": {"type": "array", "items": {"type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "sets": {"type": "integer"},
                            "reps": {"type": "string", "description": "e.g. '8-12' or '30 sec'"},
                            "duration_min": {"type": "integer"},
                            "notes": {"type": "string"}},
                        "required": ["name"]}}},
                    "required": ["day", "exercises"]}}},
            "required": ["title", "days"]}}},
]


def _profile_block(user):
    parts = []
    if user.age: parts.append(f"age {user.age}")
    if user.gender: parts.append(user.gender)
    if user.height: parts.append(f"{user.height}cm")
    if user.weight: parts.append(f"{user.weight}kg")
    line1 = f"- {user.first_name or user.username}: {', '.join(parts) or 'no physical data yet'}"
    line2 = (f"- Goal: {user.fitness_goal or 'not set'} | Level: "
             f"{user.experience_level or 'not set'} | Diet: "
             f"{user.diet_preference or 'not set'} | Workouts/week: "
             f"{user.workout_frequency or '?'}")
    line3 = f"- Injuries/limitations: {user.injuries or 'none reported'}"
    return "\n".join([line1, line2, line3])


def _search_plans(model, query, fields=("title", "description")):
    q = Q()
    for word in query.split()[:5]:
        sub = Q()
        for f in fields:
            sub |= Q(**{f"{f}__icontains": word})
        q |= sub
    return model.objects.filter(q)[:6] if q else model.objects.all()[:6]


def _run_tool(user, name, args, created_plans=None):
    try:
        if name == "create_workout_plan":
            days = args.get("days") or []
            if not isinstance(days, list) or not days:
                return json.dumps({"error": "days must be a non-empty array"})
            plan = PersonalWorkoutPlan.objects.create(
                user=user,
                title=(args.get("title") or "My AI Workout Plan")[:200],
                description=args.get("description") or "",
                goal=args.get("goal") or (user.fitness_goal or ""),
                days=days,
            )
            if created_plans is not None:
                created_plans.append({"id": plan.id, "title": plan.title})
            return json.dumps({"status": "saved", "plan_id": plan.id,
                               "note": "Plan saved to the user's My Plans page."})
        if name == "search_workouts":
            plans = _search_plans(WorkoutPlan, args.get("query", ""))
            return json.dumps([{
                "title": p.title, "duration_min": getattr(p, "workout_duration", None),
                "description": (p.description or "")[:150]} for p in plans]) or "[]"
        if name == "search_meals":
            meals = _search_plans(MealPlan, args.get("query", ""))
            return json.dumps([{
                "title": m.title, "meal_type": getattr(m, "meal_type", None),
                "is_paid": getattr(m, "is_paid", False),
                "description": (m.description or "")[:150]} for m in meals]) or "[]"
        if name == "get_my_progress":
            history = WorkoutHistory.objects.filter(user=user)
            dates = {h.date() for h in history.values_list("completed_at", flat=True)}
            week_start = date.today() - timedelta(days=date.today().weekday())
            streak, cur = 0, date.today()
            if cur not in dates:
                cur -= timedelta(days=1)
            while cur in dates:
                streak += 1
                cur -= timedelta(days=1)
            top = list(history.values("workout_plan__title")
                       .annotate(c=Count("id")).order_by("-c")[:3])
            return json.dumps({
                "total_workouts": history.count(),
                "this_week": sum(1 for d in dates if d >= week_start),
                "streak_days": streak,
                "total_minutes": history.aggregate(m=Sum("duration_minutes"))["m"] or 0,
                "favourite_plans": top,
            })
        return json.dumps({"error": "unknown tool"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _ollama_chat(messages, tools=None):
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
               "options": {"num_ctx": 8192}}
    if tools:
        payload["tools"] = tools
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["message"]


def _strip_thinking(text):
    while "<think>" in text and "</think>" in text:
        s, e = text.find("<think>"), text.find("</think>") + len("</think>")
        text = text[:s] + text[e:]
    return text.strip()


def chat(user, message, history):
    """One agent turn. history = [{'role','content'}].
    Returns (reply, tools_used, created_plans)."""
    system = SYSTEM_TEMPLATE.format(profile=_profile_block(user))
    messages = ([{"role": "system", "content": system}] + list(history)[-12:] +
                [{"role": "user", "content": message}])
    tools_used, created_plans = [], []
    try:
        for _ in range(5):
            msg = _ollama_chat(messages, tools=TOOLS)
            calls = msg.get("tool_calls") or []
            if not calls:
                return _strip_thinking(msg.get("content", "")), tools_used, created_plans
            messages.append(msg)
            for tc in calls:
                fn = tc.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tools_used.append(fn.get("name", ""))
                messages.append({"role": "tool",
                                 "content": _run_tool(user, fn.get("name", ""),
                                                      args, created_plans)})
        return "I got stuck — try rephrasing that.", tools_used, created_plans
    except Exception as e:
        return (f"I can't reach the local AI right now ({e}). "
                "Make sure Ollama is running (`ollama serve`).",
                tools_used, created_plans)
