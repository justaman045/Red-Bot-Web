from django.db import models
from django.contrib.auth import get_user_model # To get the currently active User model

User = get_user_model() # Get the User model dynamically

class RedditAPISettings(models.Model):
    """
    Model to store global Reddit API credentials for the application.
    There should only be one instance of this model.
    """
    client_id = models.CharField(max_length=255, help_text="Your Reddit Application Client ID")
    client_secret = models.CharField(max_length=255, help_text="Your Reddit Application Client Secret")
    redirect_uri = models.URLField(max_length=500, help_text="The Redirect URI configured in your Reddit App (e.g., [http://127.0.0.1:8000/reddit/callback/](http://127.0.0.1:8000/reddit/callback/))")

    class Meta:
        verbose_name = "Reddit API Settings"
        verbose_name_plural = "Reddit API Settings"

    def __str__(self):
        return "Reddit API Settings (Global)"

    def save(self, *args, **kwargs):
        # Ensure only one instance of this model exists
        if RedditAPISettings.objects.exists() and not self.pk:
            # If an instance already exists and we are trying to create a new one,
            # retrieve the existing one and update it instead.
            existing = RedditAPISettings.objects.first()
            self.pk = existing.pk
            super(RedditAPISettings, self).save(*args, **kwargs)
        else:
            super(RedditAPISettings, self).save(*args, **kwargs)


class RedditAccount(models.Model):
    """
    Model to store connected Reddit accounts for each user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reddit_accounts')
    reddit_username = models.CharField(max_length=80, unique=True)
    access_token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256, null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    scope = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f'{self.reddit_username} ({self.user.email})'

class SavedPost(models.Model):
    """
    Model to store Reddit saved posts that are queued for scheduling.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    reddit_account = models.ForeignKey(RedditAccount, on_delete=models.CASCADE, related_name='saved_posts')
    reddit_post_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=500)
    media_url = models.URLField(max_length=500, null=True, blank=True)
    post_type = models.CharField(max_length=50, null=True, blank=True)
    original_subreddit = models.CharField(max_length=100)
    created_utc = models.DateTimeField()
    scheduled_date = models.DateTimeField(null=True, blank=True)
    posted_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending') # pending, scheduled, posted, failed, skipped

    def __str__(self):
        return self.title

class SubredditSetting(models.Model):
    """
    Model to store desired subreddits for each user to cross-post to.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subreddit_setting')
    # Using JSONField for desired_subreddits for easier handling of list data
    # Requires Django 3.1+ or a separate package for older versions.
    # If using older Django, store as TextField and use json.dumps/loads manually.
    desired_subreddits = models.JSONField(default=list)

    def __str__(self):
        return f'Settings for {self.user.email}'