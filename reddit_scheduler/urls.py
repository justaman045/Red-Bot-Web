from django.urls import path
from . import views

urlpatterns = [
    path('connect/', views.connect_reddit_view, name='connect_reddit'),
    path('callback/', views.reddit_callback_view, name='reddit_callback'),
    path('accounts/<int:account_id>/delete/', views.delete_reddit_account_view, name='delete_reddit_account'),
    path('accounts/api/', views.get_reddit_accounts_api_view, name='get_reddit_accounts_api'),
    path('settings/api/', views.reddit_api_settings_view, name='reddit_api_settings'),
    path('settings/subreddits/', views.subreddit_settings_view, name='subreddit_settings'),
    path('posts/fetch_saved/', views.fetch_and_store_saved_posts_view, name='fetch_saved_posts'),
    path('posts/saved/', views.get_saved_posts_view, name='get_saved_posts'),
    path('posts/<int:post_id>/delete/', views.delete_saved_post_view, name='delete_saved_post'),
    path('posts/<int:post_id>/post-now-select-subreddits/', views.post_now_select_subreddits_view, name='post_now_select_subreddits'),
    path('posts/perform-post-now/', views.perform_post_now_view, name='perform_post_now'),
    path('posts/schedule/', views.schedule_post_view, name='schedule_post'),  # ✅ Add this line
    path('posts/', views.saved_posts_page_view, name='saved_posts_page'),
]
