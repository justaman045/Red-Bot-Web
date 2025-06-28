"""
URL configuration for Auto_Poster project.

The `urlpatterns` list routes URLs to views. For more information please see:
    [https://docs.djangoproject.com/en/5.0/topics/http/urls/](https://docs.djangoproject.com/en/5.0/topics/http/urls/)
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path, include
# from django.views.generic.base import RedirectView # For simple redirects

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('users/', include('users.urls')), # Include URLs from our users app
#     path('reddit/', include('reddit_scheduler.urls')), # Include URLs from our reddit_scheduler app
#     # Redirect root to the correct login URL within the 'users' app
#     path('', RedirectView.as_view(url='/users/login/', permanent=True)),
# ]

# your_project_name/urls.py (This is your main project's urls.py)

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Import Django's auth views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('users/', include('users.urls')), 
    path('reddit/', include('reddit_scheduler.urls')), 
    
    # Override the default login view to specify your custom template
    path('accounts/login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    # Include other auth URLs, but without the login one since we've overridden it
    path('accounts/', include('django.contrib.auth.urls')), 
    
    # You might have a root path or other app paths here too
    # path('', include('your_main_app_name.urls')), 
]
