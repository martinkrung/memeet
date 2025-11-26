#!/usr/bin/env python3
"""
Twitter Unfollower CLI Tool
Helps you unfollow inactive Twitter accounts based on their last tweet date.
"""

import os
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tweepy
from dotenv import load_dotenv


class TwitterUnfollower:
    """Manages the process of identifying and unfollowing inactive Twitter accounts."""

    CACHE_FILE = "followers_cache.json"

    def __init__(self):
        """Initialize Twitter API client."""
        load_dotenv()

        # Get API credentials from environment
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

        # Debug: Print loaded credentials (masked for security)
        print("\n" + "="*70)
        print("DEBUG: Environment variables loaded from .env")
        print("="*70)

        def mask_value(val):
            """Mask sensitive values, showing only first/last few chars."""
            if not val:
                return "❌ NOT SET"
            if len(val) <= 10:
                return f"✓ Set ({len(val)} chars)"
            return f"✓ {val[:4]}...{val[-4:]} ({len(val)} chars)"

        print(f"TWITTER_API_KEY:              {mask_value(api_key)}")
        print(f"TWITTER_API_SECRET:           {mask_value(api_secret)}")
        print(f"TWITTER_ACCESS_TOKEN:         {mask_value(access_token)}")
        print(f"TWITTER_ACCESS_TOKEN_SECRET:  {mask_value(access_token_secret)}")
        print(f"TWITTER_BEARER_TOKEN:         {mask_value(bearer_token)}")
        print("="*70 + "\n")

        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError(
                "Missing Twitter API credentials. "
                "Please set them in .env file (see .env.example)"
            )

        # Initialize Tweepy client (API v2)
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

        # Also initialize v1.1 API for unfollowing (v2 doesn't support it yet)
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

        self.me = None

    def get_authenticated_user(self):
        """Get the authenticated user's information."""
        if not self.me:
            try:
                self.me = self.client.get_me()
                print(f"\n✓ Authenticated as: @{self.me.data.username}")
            except tweepy.errors.Forbidden as e:
                print(f"\n✗ Error: 403 Forbidden - {e}")
                print("\n" + "="*70)
                print("MOST COMMON ISSUE: You're using the FREE API tier!")
                print("="*70)
                print("\n⚠️  The Twitter Free tier does NOT support:")
                print("   - Reading who you follow")
                print("   - Unfollowing users")
                print("   - Reading user tweets")
                print("\n✓  You need Twitter API BASIC tier or higher (~$100/month)")
                print("\nTo check/upgrade your API tier:")
                print("1. Go to https://developer.twitter.com/en/portal/dashboard")
                print("2. Check your subscription level")
                print("3. If it says 'Free', upgrade to Basic or higher")
                print("\n" + "-"*70)
                print("Alternative issue: App not attached to Project")
                print("-"*70)
                print("If you DO have Basic tier or higher:")
                print("1. Create a Project in Twitter Developer Portal")
                print("2. Add your app to the project")
                print("3. IMPORTANT: Regenerate your Access Token & Secret")
                print("4. Update your .env file with new tokens")
                print("\nSee README.md for detailed setup instructions.")
                print("="*70)
                raise
            except tweepy.errors.Unauthorized as e:
                print(f"\n✗ Error: 401 Unauthorized - {e}")
                print("\nYour API credentials are invalid or incorrect.")
                print("Please check your .env file and make sure:")
                print("- All credentials are correct (no typos)")
                print("- No extra spaces or quotes around values")
                print("- Tokens were regenerated after adding app to Project")
                raise
        return self.me

    def load_cache(self):
        """Load cached followers data if available."""
        cache_path = Path(self.CACHE_FILE)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    print(f"\n✓ Loaded cached data from {self.CACHE_FILE}")
                    print(f"  Cache created: {data.get('created_at', 'unknown')}")
                    return data.get('followers', [])
            except Exception as e:
                print(f"⚠ Warning: Could not load cache: {e}")
        return None

    def save_cache(self, followers):
        """Save followers data to cache."""
        data = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'followers': followers
        }
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Cached data saved to {self.CACHE_FILE}")
        except Exception as e:
            print(f"⚠ Warning: Could not save cache: {e}")

    def fetch_following(self, force_refresh=False):
        """Fetch all users that the authenticated user is following."""
        if not force_refresh:
            cached = self.load_cache()
            if cached:
                return cached

        user = self.get_authenticated_user()
        user_id = user.data.id

        print("\n⏳ Fetching all accounts you follow...")
        print("   This may take a while depending on how many accounts you follow...")

        followers_data = []
        pagination_token = None
        count = 0

        while True:
            try:
                # Fetch following with user fields and tweet fields
                response = self.client.get_users_following(
                    id=user_id,
                    max_results=1000,  # Max allowed
                    pagination_token=pagination_token,
                    user_fields=['created_at', 'description', 'public_metrics', 'username'],
                    tweet_fields=['created_at']
                )

                if not response.data:
                    break

                # For each user, get their most recent tweet
                for user in response.data:
                    count += 1
                    if count % 50 == 0:
                        print(f"   Processed {count} accounts...")

                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'name': user.name,
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                        'followers_count': user.public_metrics.get('followers_count', 0) if user.public_metrics else 0,
                        'following_count': user.public_metrics.get('following_count', 0) if user.public_metrics else 0,
                        'tweet_count': user.public_metrics.get('tweet_count', 0) if user.public_metrics else 0,
                    }

                    # Get user's most recent tweet
                    try:
                        tweets = self.client.get_users_tweets(
                            id=user.id,
                            max_results=5,
                            tweet_fields=['created_at'],
                            exclude=['retweets', 'replies']  # Only original tweets
                        )

                        if tweets.data and len(tweets.data) > 0:
                            # Get the most recent tweet
                            latest_tweet = tweets.data[0]
                            user_info['last_tweet_at'] = latest_tweet.created_at.isoformat()
                        else:
                            user_info['last_tweet_at'] = None
                    except Exception as e:
                        print(f"   ⚠ Could not fetch tweets for @{user.username}: {e}")
                        user_info['last_tweet_at'] = None

                    followers_data.append(user_info)

                # Check if there are more pages
                if 'next_token' not in response.meta:
                    break
                pagination_token = response.meta['next_token']

            except tweepy.errors.Forbidden as e:
                print(f"\n✗ Error: 403 Forbidden - {e}")
                print("\n" + "="*70)
                print("MOST COMMON ISSUE: You're using the FREE API tier!")
                print("="*70)
                print("\n⚠️  The Twitter Free tier does NOT support:")
                print("   - Reading who you follow")
                print("   - Unfollowing users")
                print("   - Reading user tweets")
                print("\n✓  You need Twitter API BASIC tier or higher (~$100/month)")
                print("\nTo check/upgrade your API tier:")
                print("1. Go to https://developer.twitter.com/en/portal/dashboard")
                print("2. Check your subscription level")
                print("3. If it says 'Free', upgrade to Basic or higher")
                print("\n" + "-"*70)
                print("Alternative issue: App not attached to Project")
                print("-"*70)
                print("If you DO have Basic tier or higher:")
                print("1. Create a Project in Twitter Developer Portal")
                print("2. Add your app to the project")
                print("3. IMPORTANT: Regenerate your Access Token & Secret")
                print("4. Update your .env file with new tokens")
                print("\nSee README.md for detailed setup instructions.")
                print("="*70)
                raise
            except Exception as e:
                print(f"\n✗ Error fetching following: {e}")
                raise

        print(f"\n✓ Fetched {len(followers_data)} accounts")

        # Save to cache
        self.save_cache(followers_data)

        return followers_data

    def filter_inactive_users(self, followers, inactive_days):
        """Filter users who haven't tweeted in the specified number of days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        inactive_users = []

        for user in followers:
            last_tweet = user.get('last_tweet_at')

            if last_tweet is None:
                # User has never tweeted or all tweets are retweets/replies
                inactive_users.append({
                    **user,
                    'inactivity_reason': 'No original tweets found'
                })
            else:
                last_tweet_date = datetime.fromisoformat(last_tweet.replace('Z', '+00:00'))
                if last_tweet_date < cutoff_date:
                    days_inactive = (datetime.now(timezone.utc) - last_tweet_date).days
                    inactive_users.append({
                        **user,
                        'inactivity_reason': f'Last tweet {days_inactive} days ago'
                    })

        return inactive_users

    def display_inactive_users(self, inactive_users):
        """Display the list of inactive users."""
        print(f"\n{'='*80}")
        print(f"Found {len(inactive_users)} inactive accounts:")
        print(f"{'='*80}\n")

        for i, user in enumerate(inactive_users, 1):
            print(f"{i}. @{user['username']} ({user['name']})")
            print(f"   └─ {user['inactivity_reason']}")
            if user.get('last_tweet_at'):
                print(f"   └─ Last tweet: {user['last_tweet_at']}")
            print()

    def unfollow_user(self, user_id, username):
        """Unfollow a specific user."""
        try:
            self.api_v1.destroy_friendship(user_id=user_id)
            print(f"   ✓ Unfollowed @{username}")
            return True
        except Exception as e:
            print(f"   ✗ Failed to unfollow @{username}: {e}")
            return False

    def interactive_unfollow(self, inactive_users):
        """Interactively unfollow users (one by one or all at once)."""
        if not inactive_users:
            print("\n✓ No inactive users to unfollow!")
            return

        print(f"\n{'='*80}")
        print("Unfollow Options:")
        print(f"{'='*80}")
        print("1. Unfollow all at once")
        print("2. Unfollow one by one (ask for each)")
        print("3. Cancel")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == '1':
            # Unfollow all
            confirm = input(f"\n⚠ Are you sure you want to unfollow ALL {len(inactive_users)} accounts? (yes/no): ").strip().lower()
            if confirm == 'yes':
                print("\n⏳ Unfollowing all accounts...")
                success_count = 0
                for user in inactive_users:
                    if self.unfollow_user(user['id'], user['username']):
                        success_count += 1
                print(f"\n✓ Successfully unfollowed {success_count}/{len(inactive_users)} accounts")
            else:
                print("\n✗ Cancelled")

        elif choice == '2':
            # Unfollow one by one
            print("\n⏳ Starting one-by-one unfollowing...")
            success_count = 0

            for i, user in enumerate(inactive_users, 1):
                print(f"\n[{i}/{len(inactive_users)}] @{user['username']} ({user['name']})")
                print(f"   {user['inactivity_reason']}")

                decision = input("   Unfollow? (y/n/q to quit): ").strip().lower()

                if decision == 'q':
                    print("\n✗ Stopped unfollowing")
                    break
                elif decision == 'y':
                    if self.unfollow_user(user['id'], user['username']):
                        success_count += 1
                else:
                    print("   ↷ Skipped")

            print(f"\n✓ Unfollowed {success_count} accounts")

        else:
            print("\n✗ Cancelled")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Twitter Unfollower CLI - Unfollow inactive accounts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find accounts inactive for 2 years (730 days)
  python twitter_unfollower.py --days 730

  # Find accounts inactive for 1 year
  python twitter_unfollower.py --days 365

  # Force refresh (ignore cache)
  python twitter_unfollower.py --days 730 --refresh

  # Just list inactive accounts without unfollowing
  python twitter_unfollower.py --days 730 --list-only
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=730,  # 2 years default
        help='Number of days of inactivity to consider (default: 730 = 2 years)'
    )

    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Force refresh data from Twitter (ignore cache)'
    )

    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list inactive accounts without unfollowing'
    )

    args = parser.parse_args()

    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          Twitter Unfollower CLI Tool                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    try:
        unfollower = TwitterUnfollower()
        unfollower.get_authenticated_user()

        # Fetch following
        followers = unfollower.fetch_following(force_refresh=args.refresh)

        # Filter inactive users
        print(f"\n⏳ Analyzing accounts for {args.days} days ({args.days // 365} years) of inactivity...")
        inactive_users = unfollower.filter_inactive_users(followers, args.days)

        # Display results
        unfollower.display_inactive_users(inactive_users)

        # Unfollow (unless list-only mode)
        if not args.list_only:
            unfollower.interactive_unfollow(inactive_users)
        else:
            print("\n(List-only mode: No accounts were unfollowed)")

    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
