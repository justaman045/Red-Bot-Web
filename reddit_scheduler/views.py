# reddit_scheduler/views.py
from venv import logger
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
import praw
import datetime
import json
from .models import RedditAccount, SavedPost, SubredditSetting, RedditAPISettings
from .forms import RedditAPISettingsForm # Import the new form
from django.urls import reverse
import datetime as dt # Import datetime with an alias to avoid conflict
from django.utils import timezone # Import Django's timezone module

# Helper function to get Reddit API credentials from DB
def get_reddit_api_credentials():
    settings = RedditAPISettings.objects.first()
    if settings:
        return settings.client_id, settings.client_secret, settings.redirect_uri
    return None, None, None

# Decorator to check if user is staff (admin)
def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# View for managing Reddit API Settings (Client ID, Secret, Redirect URI)
@login_required
@user_passes_test(is_staff_user, login_url='/users/login/') # Only staff users can access
def reddit_api_settings_view(request):
    settings_instance = RedditAPISettings.objects.first()
    if not settings_instance:
        settings_instance = RedditAPISettings() # Create a dummy instance if none exists

    if request.method == 'POST':
        form = RedditAPISettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reddit API settings updated successfully!')
            return redirect('reddit_api_settings')
        else:
            messages.error(request, 'Error saving Reddit API settings. Please check your input.')
    else:
        form = RedditAPISettingsForm(instance=settings_instance)

    context = {'form': form}
    return render(request, 'reddit_scheduler/api_settings.html', context)


# View for connecting Reddit account (initiates OAuth)
@login_required
def connect_reddit_view(request):
    client_id, client_secret, redirect_uri = get_reddit_api_credentials()
    if not client_id or not client_secret or not redirect_uri:
        messages.error(request, 'Reddit API credentials are not configured. Please contact an administrator.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Initialize Reddit with PRAW
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            user_agent="RedditPostScheduler/1.0 by Benificial_Ask"
        )

        # ✅ Ensure all necessary scopes are included
        scopes = ["*"]  # Add other scopes as needed
        auth_url = reddit.auth.url(scopes=scopes, state='unique_string_state', duration='permanent')

        return JsonResponse({"auth_url": auth_url}, status=200)

    # If GET, show connected Reddit accounts
    reddit_accounts = RedditAccount.objects.filter(user=request.user)
    context = {
        'reddit_accounts': reddit_accounts
    }
    return render(request, 'reddit_scheduler/connect_reddit.html', context)

# API endpoint to get a list of connected Reddit accounts for the current user
@login_required
def get_reddit_accounts_api_view(request):
    accounts = RedditAccount.objects.filter(user=request.user)
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            'id': account.id,
            'username': account.reddit_username,
            'scope': account.scope,
            # Do NOT expose access_token or refresh_token directly in API response
        })
    return JsonResponse({'accounts': accounts_data}) # Changed: Wrapped in a dictionary with 'accounts' key

# Callback view for Reddit OAuth
def reddit_callback_view(request):
    client_id, client_secret, redirect_uri = get_reddit_api_credentials()
    if not client_id or not client_secret or not redirect_uri:
        messages.error(request, 'Reddit API credentials are not configured. Please contact an administrator.')
        return redirect('dashboard')

    code = request.GET.get('code')
    state = request.GET.get('state')

    if not code:
        return redirect(reverse('connect_reddit') + '?error_message=Authorization code not found.')

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            user_agent="RedditPostScheduler/1.0 by Benificial_Ask"  # Replace with your actual Reddit username
        )

        # Exchange code for refresh token
        refresh_token = reddit.auth.authorize(code)
        reddit_user = reddit.user.me()
        reddit_username = reddit_user.name

        existing_account = RedditAccount.objects.filter(
            user=request.user,
            reddit_username=reddit_username
        ).first()

        if existing_account:
            existing_account.refresh_token = refresh_token or existing_account.refresh_token
            existing_account.token_expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
            existing_account.scope = ','.join(reddit.auth.scopes())
            existing_account.save()
            return redirect(reverse('connect_reddit') + '?message=Reddit account updated successfully!')
        else:
            new_reddit_account = RedditAccount(
                user=request.user,
                reddit_username=reddit_username,
                refresh_token=refresh_token,
                token_expiry=datetime.datetime.now() + datetime.timedelta(hours=1),
                scope=','.join(reddit.auth.scopes())
            )
            new_reddit_account.save()
            return redirect(reverse('connect_reddit') + '?message=Reddit account connected successfully!')

    except Exception as e:
        print(f"Error during Reddit OAuth callback: {e}")
        return redirect(reverse('connect_reddit') + f'?error_message=Failed to connect Reddit account: {e}')

# View for deleting a connected Reddit account
@login_required
def delete_reddit_account_view(request, account_id):
    if request.method == 'POST': # Using POST for deletion for security
        try:
            account = RedditAccount.objects.get(id=account_id, user=request.user)
            account.delete()
            return JsonResponse({"message": "Reddit account deleted successfully"}, status=200)
        except RedditAccount.DoesNotExist:
            return JsonResponse({"message": "Reddit account not found or unauthorized"}, status=404)
        except Exception as e:
            return JsonResponse({"message": f"Error deleting account: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request method"}, status=405)

# View for deleting a saved post
@login_required
def delete_saved_post_view(request, post_id):
    if request.method == 'POST':
        try:
            post = SavedPost.objects.get(id=post_id, user=request.user)
            post.delete()
            return JsonResponse({"message": "Saved post deleted successfully"}, status=200)
        except SavedPost.DoesNotExist:
            return JsonResponse({"message": "Saved post not found or unauthorized"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting saved post: {e}")
            return JsonResponse({"message": f"Error deleting saved post: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request method"}, status=405)

# View for deleting a saved post
@login_required
def delete_saved_post_view(request, post_id):
    if request.method == 'POST':
        try:
            post = SavedPost.objects.get(id=post_id, user=request.user)
            post.delete()
            return JsonResponse({"message": "Saved post deleted successfully"}, status=200)
        except SavedPost.DoesNotExist:
            return JsonResponse({"message": "Saved post not found or unauthorized"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting saved post: {e}")
            return JsonResponse({"message": f"Error deleting saved post: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request method"}, status=405)


# New view for selecting subreddits for immediate posting
@login_required
def post_now_select_subreddits_view(request, post_id):
    post = get_object_or_404(SavedPost, id=post_id, user=request.user)
    subreddit_setting, created = SubredditSetting.objects.get_or_create(user=request.user)
    
    context = {
        'post': post,
        'desired_subreddits_list': subreddit_setting.desired_subreddits,
    }
    return render(request, 'reddit_scheduler/select_subreddits_for_posting.html', context)

# New API endpoint for performing immediate post
@login_required
def perform_post_now_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            selected_subreddits = data.get('selected_subreddits', [])

            if not post_id or not selected_subreddits:
                return JsonResponse({"message": "Post ID and selected subreddits are required."}, status=400)
            
            if not isinstance(selected_subreddits, list) or not all(isinstance(s, str) for s in selected_subreddits):
                return JsonResponse({"message": "Selected subreddits must be a list of strings."}, status=400)

            post = get_object_or_404(SavedPost, id=post_id, user=request.user)
            reddit_account = post.reddit_account

            if not reddit_account or not reddit_account.refresh_token:
                return JsonResponse({"message": "Associated Reddit account not found or not authorized."}, status=400)

            api_settings = RedditAPISettings.objects.first()
            if not api_settings or not api_settings.client_id or not api_settings.client_secret:
                return JsonResponse({"message": "Reddit API credentials are not configured."}, status=500)

            reddit = praw.Reddit(
                client_id=api_settings.client_id,
                client_secret=api_settings.client_secret,
                refresh_token=reddit_account.refresh_token,
                user_agent=f"RedditPostScheduler/1.0 by {reddit_account.reddit_username}"
            )

            posted_to = []
            failed_to_post_to = []

            for subreddit_name in selected_subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name.strip()) # Ensure no leading/trailing spaces

                    if post.post_type == 'text':
                        submission = subreddit.submit(
                            title=post.title,
                            selftext=post.url # Assuming 'url' field might contain the selftext for text posts
                        )
                    elif post.post_type in ['link', 'image', 'video', 'media_link']:
                        submission = subreddit.submit(
                            title=post.title,
                            url=post.url # Use post.url for link/media posts
                        )
                    else:
                        failed_to_post_to.append(f"{subreddit_name} (Unsupported post type: {post.post_type})")
                        logger.warning(f"Unsupported post type '{post.post_type}' for post {post.id} to r/{subreddit_name}.")
                        continue
                    # print(f"Posting to r/{subreddit_name} with title: {post.title} and URL: {post.url}")
                    
                    posted_to.append(subreddit_name)
                    logger.info(f"Successfully posted '{post.title}' to r/{subreddit_name}. Reddit ID: {submission.id}")

                except praw.exceptions.APIException as e:
                    failed_to_post_to.append(f"{subreddit_name} (API Error: {e})")
                    logger.error(f"Reddit API Error posting '{post.title}' to r/{subreddit_name}: {e}")
                except Exception as e:
                    failed_to_post_to.append(f"{subreddit_name} (Error: {e})")
                    logger.error(f"General error posting '{post.title}' to r/{subreddit_name}: {e}")

            if posted_to:
                post.status = 'posted'
                post.posted_date = timezone.now()
                # If posting to multiple, you might want to store a list of submission IDs
                # For simplicity, we'll just update the status once.
                post.save()
                message = f"Post '{post.title}' successfully posted to: {', '.join(posted_to)}."
                if failed_to_post_to:
                    message += f" Failed to post to: {', '.join(failed_to_post_to)}."
                else:
                    # unsave the post from saved posts on reddit
                    print(f"Unsaving post {post.id} from Reddit.")
                    submission = reddit.submission(id=post.reddit_post_id)

                return JsonResponse({"message": message}, status=200)
            else:
                message = f"Failed to post '{post.title}' to any selected subreddit."
                if failed_to_post_to:
                    message += f" Details: {', '.join(failed_to_post_to)}."
                return JsonResponse({"message": message}, status=500)

        except json.JSONDecodeError:
            logger.error("JSONDecodeError in perform_post_now_view: Request body is not valid JSON.")
            return JsonResponse({"message": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            logger.error(f"Error in perform_post_now_view: {e}")
            return JsonResponse({"message": f"Failed to perform post: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request method"}, status=405)



# View for managing subreddit settings
@login_required
def subreddit_settings_view(request):
    setting, created = SubredditSetting.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            # Handle JSON submission (from fetch in JS)
            if request.content_type == 'application/json':
                body_unicode = request.body.decode('utf-8')
                print("Raw JSON POST body:", body_unicode)
                data = json.loads(body_unicode)
                desired_subreddits = data.get('desired_subreddits')

                print("Parsed subreddits from JSON:", desired_subreddits)

                if not isinstance(desired_subreddits, list):
                    return JsonResponse({"message": "desired_subreddits must be a list"}, status=400)

                setting.desired_subreddits = desired_subreddits
                setting.save()
                return JsonResponse({"message": "Subreddit settings updated successfully"}, status=200)

            # Handle regular form POST (optional)
            desired_subreddits_str = request.POST.get('desired_subreddits_json')
            print("Form submission received. Raw string:", desired_subreddits_str)

            if not desired_subreddits_str:
                return JsonResponse({"message": "No subreddit data submitted."}, status=400)

            desired_subreddits = json.loads(desired_subreddits_str)
            print("Parsed from form:", desired_subreddits)

            if not isinstance(desired_subreddits, list):
                return JsonResponse({"message": "Subreddit data must be a list"}, status=400)

            setting.desired_subreddits = desired_subreddits
            setting.save()
            return redirect('subreddit_settings')

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": "Error processing request", "error": str(e)}, status=400)

    # Handle GET request
    context = {
        'desired_subreddits_json': json.dumps(setting.desired_subreddits),
        'desired_subreddits_list': setting.desired_subreddits
    }
    return render(request, 'reddit_scheduler/subreddit_settings.html', context)

# View for fetching and storing saved posts
@login_required
def fetch_and_store_saved_posts_view(request):
    client_id, client_secret, redirect_uri = get_reddit_api_credentials()
    if not client_id or not client_secret or not redirect_uri:
        return JsonResponse({"message": "Reddit API credentials are not configured."}, status=500)

    if request.method != 'POST':
        return JsonResponse({"message": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        reddit_account_id = data.get('reddit_account_id')

        if not reddit_account_id:
            return JsonResponse({"message": "Reddit account ID is required"}, status=400)

        reddit_account = RedditAccount.objects.filter(
            id=reddit_account_id,
            user=request.user
        ).first()

        if not reddit_account:
            return JsonResponse({"message": "Reddit account not found or unauthorized"}, status=404)

        # Initialize Reddit instance
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=reddit_account.refresh_token,
            user_agent="RedditPostScheduler/1.0 by Benificial_Ask"
        )

        # Optional: Debug scopes
        try:
            print("Authorized scopes:", reddit.auth.scopes())
        except Exception as scope_error:
            print("Error retrieving scopes:", scope_error)

        # Try to fetch saved posts
        try:
            saved_posts = reddit.user.me().saved(limit=None)
        except Exception as e:
            return JsonResponse({"message": "Access denied. The refresh token may lack 'read' scope or is invalid."}, status=403)

        new_posts_count = 0
        updated_posts_count = 0

        for post in saved_posts:
            try:
                existing_saved_post = SavedPost.objects.filter(
                        reddit_post_id=post.id,
                        user=request.user
                    ).first()
                if existing_saved_post:
                    updated_posts_count += 1
                    continue
            except Exception as e:
                print(f"Error checking existing saved post: {e}")

            media_url = None
            post_type = 'link'
            if hasattr(post, 'is_video') and post.is_video:
                if hasattr(post, 'media') and post.media and 'reddit_video' in post.media:
                    media_url = post.media['reddit_video']['fallback_url']
                elif hasattr(post, 'url') and ('redgifs.com' in post.url or 'gfycat.com' in post.url):
                    media_url = post.url
                post_type = 'video'
            elif hasattr(post, 'is_reddit_media_domain') and post.is_reddit_media_domain:
                if hasattr(post, 'url_overridden_by_dest'):
                    media_url = post.url_overridden_by_dest
                post_type = 'image' if 'i.redd.it' in post.url else 'media_link'
            elif hasattr(post, 'url') and (post.url.endswith('.jpg') or post.url.endswith('.png') or post.url.endswith('.gif')):
                media_url = post.url
                post_type = 'image'
            elif hasattr(post, 'selftext') and post.selftext:
                post_type = 'text'

            new_saved_post = SavedPost(
                user=request.user,
                reddit_account=reddit_account,
                reddit_post_id=post.id,
                title=post.title,
                url=post.url,
                media_url=media_url,
                post_type=post_type,
                original_subreddit=post.subreddit.display_name,
                created_utc=datetime.datetime.utcfromtimestamp(post.created_utc).replace(tzinfo=datetime.timezone.utc),
                status='pending'
            )
            new_saved_post.save()
            new_posts_count += 1

        return JsonResponse({
            "message": f"Successfully fetched and stored {new_posts_count} new saved posts and updated {updated_posts_count} existing.",
            "new_posts_count": new_posts_count,
            "updated_posts_count": updated_posts_count
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error fetching and storing saved posts: {e}")
        return JsonResponse({"message": f"Failed to fetch or store saved posts: {str(e)}"}, status=500)


# View for retrieving saved posts
@login_required
def get_saved_posts_view(request):
    status_filter = request.GET.get('status')
    query = SavedPost.objects.filter(user=request.user)

    if status_filter:
        query = query.filter(status=status_filter)

    saved_posts = query.order_by('-created_utc') # Order by creation date descending

    posts_data = []
    for post in saved_posts:
        posts_data.append({
            "id": post.id,
            "reddit_post_id": post.reddit_post_id,
            "title": post.title,
            "url": post.url,
            "media_url": post.media_url,
            "post_type": post.post_type,
            "original_subreddit": post.original_subreddit,
            "created_utc": post.created_utc.isoformat(),
            "scheduled_date": post.scheduled_date.isoformat() if post.scheduled_date else None,
            "posted_date": post.posted_date.isoformat() if post.posted_date else None,
            "status": post.status,
            "reddit_account_id": post.reddit_account.id
        })
    return JsonResponse({"posts": posts_data}, status=200)

# View for scheduling a post
@login_required
def schedule_post_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Ensure the parsed data is a dictionary
            if not isinstance(data, dict):
                print(f"Received non-dictionary JSON data: {data}")
                return JsonResponse({"message": "Invalid request body format. Expected JSON object."}, status=400)

            post_id = data.get('post_id')
            scheduled_date_str = data.get('scheduled_date')

            if not post_id or not scheduled_date_str:
                return JsonResponse({"message": "Post ID and scheduled date are required"}, status=400)

            try:
                # Handle 'Z' suffix for UTC before parsing with fromisoformat
                if scheduled_date_str.endswith('Z'):
                    # Remove 'Z' and treat as naive UTC, then make_aware
                    naive_scheduled_date = dt.datetime.fromisoformat(scheduled_date_str[:-1])
                    scheduled_date = timezone.make_aware(naive_scheduled_date)
                else:
                    # Parse as is, and make it aware using default timezone if naive
                    naive_scheduled_date = dt.datetime.fromisoformat(scheduled_date_str)
                    scheduled_date = timezone.make_aware(naive_scheduled_date)
            except ValueError as e:
                print(f"Invalid scheduled_date format. Error: {e}")
                return JsonResponse({"message": "Invalid scheduled_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS) or (YYYY-MM-DDTHH:MM:SS.sssZ)."}, status=400)
            except Exception as e:
                print(f"Unexpected error during date parsing/timezone conversion: {e}")
                return JsonResponse({"message": f"Failed to process scheduled date: {e}"}, status=500)

            post = SavedPost.objects.filter(id=post_id, user=request.user).first()

            if not post:
                return JsonResponse({"message": "Post not found or unauthorized"}, status=404)

            if post.status == 'posted':
                return JsonResponse({"message": "This post has already been published."}, status=400)

            post.scheduled_date = scheduled_date
            post.status = 'scheduled'
            post.save()

            return JsonResponse({"message": f"Post '{post.title}' scheduled successfully for {scheduled_date.isoformat()}"}, status=200)
        except json.JSONDecodeError:
            print("JSONDecodeError: Request body is not valid JSON.")
            return JsonResponse({"message": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            print(f"Error scheduling post: {e}")
            return JsonResponse({"message": f"Failed to schedule post: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request method"}, status=405)

# View for Saved Posts (HTML rendering)
@login_required
def saved_posts_page_view(request):
    # This view fetches data and passes it to the template
    # The actual fetching logic is in get_saved_posts_view (API endpoint)
    # For simplicity, we'll call the API view internally or just pass an empty list
    # and let JS fetch it.
    
    # Option 1: Fetch data directly in Django view (less common for dynamic UIs)
    # saved_posts_response = get_saved_posts_view(request)
    # saved_posts_data = json.loads(saved_posts_response.content)['posts']

    # Option 2: Let frontend JS fetch data after page load (more common for SPAs/dynamic content)
    context = {
        'initial_posts_data': '[]' # Placeholder, JS will fetch
    }
    return render(request, 'reddit_scheduler/saved_posts.html', context)