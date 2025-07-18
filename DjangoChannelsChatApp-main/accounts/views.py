from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, AnswerAuthForm, ResetPasswordForm
from .models import Profile

# Create your views here.

def user_login(request):
    """
    Handles user login: processes form data, authenticates, and logs in the user.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {username}! You are now logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def user_register(request):
    """
    Handles user registration: creates a new user if passwords match and username is unique.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile with security question and answer
            profile = Profile.objects.create(
                user=user,
                security_question=form.cleaned_data['security_question'],
                security_answer=form.cleaned_data['security_answer']
            )
            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def answer_auth_view(request):
    """
    Handles security question authentication for password recovery.
    """
    if request.method == 'POST':
        form = AnswerAuthForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)
            
            # Store user info in session for password reset
            request.session['reset_username'] = username
            request.session['security_question'] = profile.security_question
            
            messages.success(request, "Security question verified. Please reset your password.")
            return redirect('reset_password')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AnswerAuthForm()
    
    return render(request, 'accounts/answer_auth.html', {'form': form})

def reset_password_view(request):
    """
    Handles password reset after security question verification.
    """
    # Check if user has completed security question verification
    if 'reset_username' not in request.session:
        messages.error(request, "Please complete security question verification first.")
        return redirect('answer_auth')
    
    username = request.session['reset_username']
    security_question = request.session.get('security_question')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(username=username)
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Clear session data
            del request.session['reset_username']
            del request.session['security_question']
            
            messages.success(request, "Password reset successful! Please log in with your new password.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ResetPasswordForm()
    
    # Get the question text for display
    question_text = dict(Profile.SECURITY_QUESTIONS).get(security_question, security_question)
    
    context = {
        'form': form,
        'username': username,
        'security_question': question_text
    }
    return render(request, 'accounts/reset_password.html', context)

def user_logout(request):
    """
    This function handles user logout.
    It uses Django's built-in logout function.
    """
    logout(request) # Log out the current user
    messages.info(request, "You have been logged out.") # Optional: add a success message
    return redirect('login') # Redirect to the login page after logout
