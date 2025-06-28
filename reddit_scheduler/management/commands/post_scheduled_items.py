# reddit_scheduler/management/commands/post_scheduled_items.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from reddit_scheduler.models import SavedPost, RedditAccount, RedditAPISettings
import praw
import datetime as dt
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Posts scheduled Reddit items that are due.'

    def handle(self, *args, **options):
        # Fetch Reddit API credentials from DB
        api_settings = RedditAPISettings.objects.first()
        if not api_settings:
            logger.error("Reddit API credentials not configured. Cannot post scheduled items.")
            raise CommandError('Reddit API credentials not configured. Cannot post scheduled items.')

        client_id = api_settings.client_id
        client_secret = api_settings.client_secret
        redirect_uri = api_settings.redirect_uri # Not strictly needed for refresh token flow, but good to have

        if not client_id or not client_secret:
            logger.error("Client ID or Client Secret missing from Reddit API Settings.")
            raise CommandError('Client ID or Client Secret missing from Reddit API Settings.')

        # Get current time, ensuring it's timezone-aware
        now = timezone.now()

        # Find posts that are scheduled and whose scheduled_date is in the past or current
        # Note: Avoid using __lte with timezone.now() directly in complex queries
        # if you encounter issues, fetch and filter in Python.
        # For simplicity, we assume scheduled_date is timezone-aware UTC.
        posts_to_post = SavedPost.objects.filter(
            status='scheduled',
            scheduled_date__lte=now
        ).select_related('reddit_account') # Optimize by pre-fetching related RedditAccount

        if not posts_to_post.exists():
            self.stdout.write(self.style.SUCCESS('No scheduled posts are due at this time.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {posts_to_post.count()} posts to attempt to post.'))

        for post in posts_to_post:
            try:
                reddit_account = post.reddit_account
                if not reddit_account.refresh_token:
                    logger.warning(f"Skipping post {post.id} (Title: '{post.title}'): No refresh token for account {reddit_account.reddit_username}.")
                    post.status = 'failed'
                    post.save()
                    continue

                reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=reddit_account.refresh_token,
                    user_agent=f"RedditPostScheduler/1.0 by {reddit_account.reddit_username}" # Use actual username
                )

                # Get the target subreddit. You might want to allow users to specify
                # a target subreddit for each post, or use the original_subreddit.
                # For this example, we'll use the original_subreddit.
                # If you have a SubredditSetting, you'd integrate that logic here.
                target_subreddit_name = post.original_subreddit
                if not target_subreddit_name:
                    logger.warning(f"Skipping post {post.id} (Title: '{post.title}'): No target subreddit specified.")
                    post.status = 'failed'
                    post.save()
                    continue

                subreddit = reddit.subreddit(target_subreddit_name)

                # Determine post type and submit
                if post.post_type == 'text':
                    submission = subreddit.submit(
                        title=post.title,
                        selftext=post.url # Assuming 'url' field might contain the selftext for text posts
                    )
                elif post.post_type == 'link' or post.post_type == 'image' or post.post_type == 'video' or post.post_type == 'media_link':
                    submission = subreddit.submit(
                        title=post.title,
                        url=post.url # Use post.url for link/media posts
                    )
                else:
                    logger.warning(f"Unsupported post type '{post.post_type}' for post {post.id} (Title: '{post.title}').")
                    post.status = 'failed'
                    post.save()
                    continue

                post.status = 'posted'
                post.posted_date = timezone.now()
                post.reddit_post_id = submission.id # Store the actual Reddit submission ID
                post.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully posted '{post.title}' to r/{target_subreddit_name}. Reddit ID: {submission.id}"))

            except praw.exceptions.APIException as e:
                logger.error(f"Reddit API Error posting '{post.title}': {e}")
                post.status = 'failed'
                post.save()
            except Exception as e:
                logger.error(f"General error posting '{post.title}': {e}")
                post.status = 'failed'
                post.save()

        self.stdout.write(self.style.SUCCESS('Scheduled post processing complete.'))