from django.shortcuts import redirect
from django.contrib import messages
from .models import EmailVerification


def role_required():
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                email_verification = EmailVerification.objects.get(
                    user=request.user)
                if not email_verification.is_verified:
                    messages.error(
                        request, "Please verify your email address.")
                    return redirect('verify')
            except EmailVerification.DoesNotExist:
                messages.error(request, "Email verification not found.")
                return redirect('verify')
            if not request.user.isProfileComplete:
                messages.error(request, "Please complete your profile.")
                return redirect('profile_complete')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator




