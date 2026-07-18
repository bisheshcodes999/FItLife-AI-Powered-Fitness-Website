"""AI Coach chatbot views."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .. import chatbot


@login_required
def coach_view(request):
    return render(request, "coach.html")


@login_required
@require_POST
def coach_chat_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "empty message"}, status=400)
    history = data.get("history") or []
    # keep only well-formed text turns
    history = [h for h in history
               if isinstance(h, dict) and h.get("role") in ("user", "assistant")
               and isinstance(h.get("content"), str)][-12:]
    reply, tools_used, created_plans = chatbot.chat(request.user, message, history)
    return JsonResponse({"reply": reply, "tools_used": tools_used,
                         "created_plans": created_plans})
