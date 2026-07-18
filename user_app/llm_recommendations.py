"""Meal recommendations via a LOCAL LLM (Ollama) — no API key, fully private.

Drop-in replacement for the old Gemini service: exposes
`meal_recommendation_service` with `get_recommended_meals(user, limit)` and
`get_ai_query_recommendations(user, query, limit)`.

Requires Ollama running locally (https://ollama.com) with a model pulled,
e.g. `ollama pull qwen3:8b`. Configure via env vars OLLAMA_URL / OLLAMA_MODEL.
"""

import json
import os
import urllib.request

from .models import MealPlan

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").strip().rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b").strip()


def _ollama_generate(prompt: str, timeout: int = 300) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_ctx": 8192},
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"].get("content", "")


def _strip_thinking(text: str) -> str:
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        text = text[:start] + text[end:]
    return text.strip()


def _extract_json_array(text: str):
    """Pull the first JSON array out of model output (handles fences/prose)."""
    text = _strip_thinking(text)
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []


class MealRecommendationService:
    def get_user_profile_data(self, user):
        return {
            "age": user.age, "gender": user.gender, "weight": user.weight,
            "height": user.height, "fitness_goal": user.fitness_goal,
            "experience_level": user.experience_level,
            "diet_preference": user.diet_preference,
            "workout_frequency": user.workout_frequency,
            "injuries": user.injuries,
            "subscription_type": user.subscription_type,
        }

    def get_available_meals_data(self):
        meals = MealPlan.objects.all().values(
            "id", "title", "description", "meal_type", "is_paid")
        return list(meals)

    def _build_prompt(self, user, limit, custom_query=None):
        p = self.get_user_profile_data(user)
        meals = self.get_available_meals_data()
        if not meals:
            return None
        profile_lines = "\n".join(
            f"- {k.replace('_', ' ').title()}: {v}"
            for k, v in p.items() if v not in (None, ""))
        query_block = (f'\nUSER QUERY: "{custom_query}"\n'
                       "Recommend meals that best answer this query, "
                       "considering the profile." if custom_query else
                       "\nRecommend meals that best match this user's profile "
                       "and fitness goal.")
        return f"""You are a professional nutritionist. Recommend meal plans
from this database ONLY:

{json.dumps(meals, indent=1, default=str)}

USER PROFILE:
{profile_lines or '- (minimal profile — recommend popular balanced meals)'}
{query_block}

Rules:
- weight_loss goal -> lower calorie, high protein meals
- muscle_gain -> high protein, balanced carbs
- respect diet_preference (veg = no meat/fish)
- free-subscription users should mostly get is_paid=false meals
- rank by relevance, return at most {limit}

Respond with ONLY a JSON array, no other text, no markdown fences:
[{{"meal_id": <id>, "relevance_score": <0.0-1.0>, "reason": "<short reason>"}}]"""

    def generate_meal_recommendations(self, user, limit=6, custom_query=None):
        try:
            prompt = self._build_prompt(user, limit, custom_query)
            if prompt is None:
                return []
            raw = _ollama_generate(prompt)
            recs = _extract_json_array(raw)
            meal_ids = set(MealPlan.objects.values_list("id", flat=True))
            valid = [r for r in recs
                     if isinstance(r, dict) and r.get("meal_id") in meal_ids]
            return valid[:limit]
        except Exception as e:
            print(f"[llm_recommendations] Ollama unavailable or failed: {e}")
            return self._fallback_recommendations(user, limit)

    def _fallback_recommendations(self, user, limit):
        """Rule-based fallback when Ollama is not running."""
        qs = MealPlan.objects.all()
        if user.subscription_type in ("none", "basic"):
            qs = qs.order_by("is_paid")
        recs = []
        for meal in qs[:limit]:
            recs.append({"meal_id": meal.id, "relevance_score": 0.5,
                         "reason": "Popular pick (AI offline — start Ollama "
                                   "for personalized recommendations)"})
        return recs

    def get_recommended_meals(self, user, limit=6):
        return self._process(self.generate_meal_recommendations(user, limit))

    def get_ai_query_recommendations(self, user, query, limit=6):
        return self._process(
            self.generate_meal_recommendations(user, limit, custom_query=query))

    def _process(self, recommendations):
        if not recommendations:
            return []
        meal_dict = {m.id: m for m in MealPlan.objects.filter(
            id__in=[r["meal_id"] for r in recommendations])}
        out = []
        for rec in recommendations:
            meal = meal_dict.get(rec["meal_id"])
            if meal:
                meal.relevance_score = rec.get("relevance_score", 0.0) * 100
                meal.recommendation_reason = rec.get("reason", "")
                out.append(meal)
        out.sort(key=lambda m: m.relevance_score, reverse=True)
        return out


meal_recommendation_service = MealRecommendationService()
