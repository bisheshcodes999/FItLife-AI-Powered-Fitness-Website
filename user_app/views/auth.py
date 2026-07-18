from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from ..models import CustomUser, EmailVerification
from django.contrib.auth.hashers import make_password
from ..decorators import role_required
from django.core.mail import send_mail
from django.conf import settings
import random
import uuid
from django.utils import timezone
from datetime import timedelta

# verification code for the 6 digit code
def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_verification_email(email, code):
    subject = "Verify your email address"
    message = f"This is your email verification code: {code}"
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        # SMTP not configured / offline — don't crash registration.
        # The code is printed to the server console so dev flow still works.
        print(f"[email] Could not send verification email: {e}")
    print(f"Verification code for {email}: {code}")



def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'auth/login.html')
        
        # Get the user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'auth/login.html')
        
        # Check the password
        if user.check_password(password):
            if user.is_active:
                auth_login(request, user)
                messages.success(request, "Login successful!")

                # check the user is verified or not (record may not exist for
                # superusers / seeded accounts — treat those as verified)
                check_email_verification = EmailVerification.objects.filter(user=user).first()
                if check_email_verification is None:
                    if user.is_staff or user.is_superuser:
                        EmailVerification.objects.create(user=user, is_verified=True)
                    else:
                        messages.error(request, "Please verify your email address.")
                        return redirect('verify')
                elif not check_email_verification.is_verified:
                    messages.error(request, "Please verify your email address.")
                    return redirect('verify')

                return redirect('home')
            else:
                messages.error(request, "Your account is not active.")
                return render(request, 'auth/login.html')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'auth/login.html')
    
    return render(request, 'auth/login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, "Logout successful!")
    return redirect('home')


def register(request):
    if request.method == "POST":
        firstName = request.POST.get("firstName")
        lastName = request.POST.get("lastName")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmPassword = request.POST.get("confirm_password")
        # Extra fields from multi‑step form
        goal = request.POST.get("goal")
        gender = request.POST.get("gender")
        age = request.POST.get("age")
        height = request.POST.get("height")
        heightUnit = request.POST.get("heightUnit")
        weight = request.POST.get("weight")
        weightUnit = request.POST.get("weightUnit")
        bodyType = request.POST.get("bodyType")  # not used in the model

        # Basic validations
        if not firstName or not lastName or not email or not password or not confirmPassword:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "auth/register.html")
            
        if password != confirmPassword:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/register.html")
            
        # Password validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "auth/register.html")
            
        if not any(char.isupper() for char in password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return render(request, "auth/register.html")
            
        if not any(not char.isalnum() for char in password):
            messages.error(request, "Password must contain at least one special character.")
            return render(request, "auth/register.html")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email address is already registered.")
            return render(request, "auth/register.html")

        # Map goal text from UI to the user model fitness_goal choices.
        mapped_goal = None
        if goal:
            if goal.lower() == "lose weight":
                mapped_goal = "weight_loss"
            elif goal.lower() == "build muscle":
                mapped_goal = "muscle_gain"
            elif goal.lower() == "get fitter":
                mapped_goal = "general_health"

        # Hash the password
        hashed_password = make_password(password)

        try:
            # Create a new user
            user = CustomUser.objects.create(
                username=email,
                email=email,
                password=hashed_password,
                first_name=firstName,
                last_name=lastName,
            )
            # Set additional fields (convert to proper types if given)
            user.gender = gender
            if age:
                try:
                    user.age = int(age)
                except ValueError:
                    user.age = None
            if height:
                try:
                    user.height = float(height)
                except ValueError:
                    user.height = None
            if weight:
                try:
                    user.weight = float(weight)
                except ValueError:
                    user.weight = None
            user.fitness_goal = mapped_goal
            user.save()

            # Create an email verification instance.
            verification_code = generate_verification_code()
            EmailVerification.objects.create(user=user, code=verification_code)
            send_verification_email(email, verification_code)

            messages.success(
                request, "Email verification sent. Please check your email."
            )
            return redirect("login")

        except Exception as e:
            messages.error(
                request, f"An error occurred during registration: {e}"
            )
            return render(request, "auth/register.html")

    return render(request, "auth/register.html")


def verify(request):

    if request.method == 'POST':
        # get the email from the session 
        email = request.user.email
        verification_code = request.POST.get('verification_code')

        # get the user by email
        user = CustomUser.objects.get(email=email)
        email_verification = EmailVerification.objects.get(user=user)

        if email_verification.code == verification_code:
            email_verification.is_verified = True
            email_verification.save()
            messages.success(request, "Email verified successfully!")
            return redirect('home')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
            return redirect('verify')
    return render(request, 'auth/verify.html')


@role_required()
def profile_complete(request):
    if request.method == 'POST':
        user = request.user
        try:
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            age = request.POST.get('age')
            user.height = float(height) if height else None
            user.weight = float(weight) if weight else None
            user.age = int(age) if age else None
        except ValueError:
            messages.error(request, "Invalid input for numeric fields.")
            return render(request, 'profile_complete.html', {'user': user})
        
        # Process text and choice fields
        user.gender = request.POST.get('gender')
        user.bio = request.POST.get('bio')
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES.get('profile_picture')
        user.fitness_goal = request.POST.get('fitness_goal')
        user.experience_level = request.POST.get('experience_level')
        workout_frequency = request.POST.get('workout_frequency')
        try:
            user.workout_frequency = int(workout_frequency) if workout_frequency else None
        except ValueError:
            user.workout_frequency = None
        user.diet_preference = request.POST.get('diet_preference')
        user.injuries = request.POST.get('injuries')
        
        # Mark the profile as complete
        user.isProfileComplete = True
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('home')
    else:
        # If GET, render the form populated with current user data.
        return render(request, 'auth/profile_complete.html', {'user': request.user})

