from django.contrib import admin
from .models import RedditAccount, SavedPost, SubredditSetting, RedditAPISettings

# Register your models here.
admin.site.register(RedditAccount)
admin.site.register(SavedPost)
admin.site.register(SubredditSetting)

# Register RedditAPISettings
@admin.register(RedditAPISettings)
class RedditAPISettingsAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'redirect_uri')
    fields = ('client_id', 'client_secret', 'redirect_uri')

    def has_add_permission(self, request):
        # Allow adding only if no instance exists
        return not RedditAPISettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the single instance
        return False