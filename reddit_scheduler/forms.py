from django import forms
from .models import RedditAPISettings

class RedditAPISettingsForm(forms.ModelForm):
    class Meta:
        model = RedditAPISettings
        fields = ['client_id', 'client_secret', 'redirect_uri']
        widgets = {
            'client_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500'}),
            'client_secret': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500'}),
            'redirect_uri': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500'}),
        }
        labels = {
            'client_id': 'Reddit Application Client ID',
            'client_secret': 'Reddit Application Client Secret',
            'redirect_uri': 'Reddit Application Redirect URI',
        }
        help_texts = {
            'client_id': 'Obtain this from your Reddit app settings (e.g., https://www.reddit.com/prefs/apps/)',
            'client_secret': 'Obtain this from your Reddit app settings',
            'redirect_uri': 'This must exactly match the "redirect uri" set in your Reddit app settings. For local development, it\'s typically http://127.0.0.1:8000/reddit/callback/. For PythonAnywhere, it will be https://your_username.pythonanywhere.com/reddit/callback/',
        }
