from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

# View for user registration
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in immediately after registration
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'message': 'User registered successfully', 'user_id': user.id}, status=201)
            return redirect('dashboard') # Redirect to dashboard after successful registration
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return form errors as JSON for API clients
                return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# View for user login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user) # Log the user in
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Login successful', 'user_id': user.id}, status=200)
            return redirect('dashboard') # Redirect to dashboard after successful login
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=401)
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# View for user logout
@login_required
def logout_view(request):
    logout(request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'message': 'Logged out successfully'}, status=200)
    return redirect('login') # Redirect to login page after logout

# View to check user status (for potential API use)
def user_status_view(request):
    if request.user.is_authenticated:
        return JsonResponse({"is_logged_in": True, "user_id": request.user.id, "email": request.user.email}, status=200)
    else:
        return JsonResponse({"is_logged_in": False}, status=200)

# Dashboard view (requires login)
@login_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')
