"""DEPRECATED — replaced by llm_recommendations.py (local Ollama, no API key).

This module previously contained a hardcoded Gemini API key. That key was
exposed in source control and should be considered compromised: revoke it at
https://aistudio.google.com/apikey.

Kept as a shim so any old imports keep working.
"""

from .llm_recommendations import (  # noqa: F401
    MealRecommendationService,
    meal_recommendation_service,
)
