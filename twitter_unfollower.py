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

    def test_api_access(self):
        """Test if the API tier supports required operations."""
        print("\n" + "="*70)
        print("Testing API Access Level...")
        print("="*70)

        user = self.get_authenticated_user()
        user_id = user.data.id

        # Test 1: Can we read our own tweets?
        print("\n[Test 1/2] Testing if we can read tweets...")
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=5,
                tweet_fields=['created_at']
            )
            print("✓ SUCCESS: Can read tweets")
        except tweepy.errors.Forbidden as e:
            print("✗ FAILED: Cannot read tweets")
            print("\n" + "="*70)
            print("⚠️  API ACCESS INSUFFICIENT - You likely have FREE tier")
            print("="*70)
            print("\nThe Free tier does NOT support:")
            print("  - Reading tweets")
            print("  - Reading follows/followers")
            print("  - Unfollowing users")
            print("\nYou need to upgrade to Basic tier ($100/month) or higher.")
            print("Upgrade at: https://developer.twitter.com/en/portal/products")
            print("="*70)
            raise ValueError("Insufficient API access. Basic tier or higher required.")

        # Test 2: Can we read who we follow?
        print("[Test 2/2] Testing if we can read following list...")
        try:
            following = self.client.get_users_following(
                id=user_id,
                max_results=5
            )
            print("✓ SUCCESS: Can read following list")
        except tweepy.errors.Forbidden as e:
            print("✗ FAILED: Cannot read following list")
            print("\n" + "="*70)
            print("⚠️  API ACCESS INSUFFICIENT - You likely have FREE tier")
            print("="*70)
            print("\nThe Free tier does NOT support reading follows/followers.")
            print("\nYou need to upgrade to Basic tier ($100/month) or higher.")
            print("Upgrade at: https://developer.twitter.com/en/portal/products")
            print("="*70)
            raise ValueError("Insufficient API access. Basic tier or higher required.")

        print("\n" + "="*70)
        print("✓ API Access Check PASSED - You have sufficient access!")
        print("="*70)
        return True

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
                # Show example user from cache
                if cached:
                    self.show_example_user(cached[0])
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

                    # Get user's most recent tweets (last 2)
                    user_info['recent_tweets'] = []
                    try:
                        tweets = self.client.get_users_tweets(
                            id=user.id,
                            max_results=5,
                            tweet_fields=['created_at', 'text'],
                            exclude=['retweets', 'replies']  # Only original tweets
                        )

                        if tweets.data and len(tweets.data) > 0:
                            # Store last 2 tweets with text
                            for tweet in tweets.data[:2]:
                                user_info['recent_tweets'].append({
                                    'text': tweet.text,
                                    'created_at': tweet.created_at.isoformat()
                                })
                            # Keep last_tweet_at for filtering
                            user_info['last_tweet_at'] = tweets.data[0].created_at.isoformat()
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

        # Show example user with all properties
        if followers_data:
            self.show_example_user(followers_data[0])

        return followers_data

    def show_example_user(self, user):
        """Display an example user with all available properties."""
        print("\n" + "="*70)
        print("EXAMPLE USER DATA - All Available Properties")
        print("="*70)
        print("\nThis shows what data you can filter/search on:\n")

        # Format the user data nicely
        print(f"📊 User ID:           {user.get('id')}")
        print(f"👤 Username:          @{user.get('username')}")
        print(f"📝 Name:              {user.get('name')}")
        print(f"📅 Account Created:   {user.get('created_at')}")
        print(f"👥 Followers:         {user.get('followers_count'):,}")
        print(f"➡️  Following:         {user.get('following_count'):,}")
        print(f"📱 Total Tweets:      {user.get('tweet_count'):,}")

        if user.get('last_tweet_at'):
            last_tweet_date = datetime.fromisoformat(user['last_tweet_at'].replace('Z', '+00:00'))
            days_ago = (datetime.now(timezone.utc) - last_tweet_date).days
            print(f"🕒 Last Tweet:        {user.get('last_tweet_at')} ({days_ago} days ago)")
        else:
            print(f"🕒 Last Tweet:        None found")

        print(f"\n📝 Recent Tweets ({len(user.get('recent_tweets', []))}):")
        if user.get('recent_tweets'):
            for i, tweet in enumerate(user.get('recent_tweets', []), 1):
                tweet_date = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - tweet_date).days
                text = tweet['text'][:80] + "..." if len(tweet['text']) > 80 else tweet['text']
                print(f"   [{i}] {days_ago} days ago: {text}")
        else:
            print("   (No recent tweets)")

        print("\n" + "="*70)
        print("These properties are available for filtering and review")
        print("="*70 + "\n")

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

    def show_user_tweets(self, user):
        """Display user's recent tweets."""
        print(f"\n   📝 Recent tweets:")
        if user.get('recent_tweets') and len(user['recent_tweets']) > 0:
            for i, tweet in enumerate(user['recent_tweets'], 1):
                tweet_date = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - tweet_date).days
                # Truncate long tweets
                text = tweet['text']
                if len(text) > 100:
                    text = text[:100] + "..."
                print(f"      [{i}] {days_ago} days ago: {text}")
        else:
            print("      (No tweets found)")

    def interactive_review(self, inactive_users):
        """Interactively review users and build unfollow list."""
        if not inactive_users:
            print("\n✓ No inactive users found!")
            return []

        print(f"\n{'='*80}")
        print("Review Mode: Build Unfollow List")
        print(f"{'='*80}")
        print("\nOptions for each account:")
        print("  y = Mark for unfollow")
        print("  n = Skip this account")
        print("  a = Mark ALL remaining for unfollow")
        print("  s = Skip all remaining and finish")
        print("  q = Quit without saving")
        print(f"{'='*80}\n")

        to_unfollow = []

        for i, user in enumerate(inactive_users, 1):
            print(f"\n[{i}/{len(inactive_users)}] @{user['username']} ({user['name']})")
            print(f"   └─ {user['inactivity_reason']}")

            # Show last 2 tweets
            self.show_user_tweets(user)

            decision = input("\n   Decision (y/n/a/s/q): ").strip().lower()

            if decision == 'q':
                print("\n✗ Quit - discarding list")
                return []
            elif decision == 's':
                print(f"\n⏩ Skipping remaining {len(inactive_users) - i} accounts")
                break
            elif decision == 'a':
                # Mark all remaining
                print(f"\n✓ Marking all remaining {len(inactive_users) - i + 1} accounts for unfollow")
                to_unfollow.extend(inactive_users[i-1:])
                break
            elif decision == 'y':
                to_unfollow.append(user)
                print(f"   ✓ Marked for unfollow ({len(to_unfollow)} total)")
            else:
                print("   ↷ Skipped")

        return to_unfollow

    def save_unfollow_list(self, to_unfollow, filename="unfollow_list.json"):
        """Save unfollow list to JSON file."""
        data = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'total_count': len(to_unfollow),
            'accounts': [
                {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'inactivity_reason': user['inactivity_reason'],
                    'last_tweet_at': user.get('last_tweet_at'),
                    'recent_tweets': user.get('recent_tweets', [])
                }
                for user in to_unfollow
            ]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Unfollow list saved to: {filename}")
            print(f"   You can edit this file and execute it later with:")
            print(f"   python twitter_unfollower.py --execute {filename}")
            return True
        except Exception as e:
            print(f"\n✗ Error saving unfollow list: {e}")
            return False

    def execute_unfollow_list(self, filename="unfollow_list.json"):
        """Execute unfollows from a saved JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            accounts = data.get('accounts', [])
            if not accounts:
                print("\n⚠ No accounts in the unfollow list")
                return

            print(f"\n{'='*80}")
            print(f"Loaded unfollow list: {len(accounts)} accounts")
            print(f"Created: {data.get('created_at', 'unknown')}")
            print(f"{'='*80}\n")

            confirm = input(f"Execute unfollows for {len(accounts)} accounts? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("\n✗ Cancelled")
                return

            print("\n⏳ Executing unfollows...")
            success_count = 0
            failed = []

            for account in accounts:
                if self.unfollow_user(account['id'], account['username']):
                    success_count += 1
                else:
                    failed.append(account['username'])

            print(f"\n{'='*80}")
            print(f"✓ Successfully unfollowed {success_count}/{len(accounts)} accounts")
            if failed:
                print(f"✗ Failed to unfollow {len(failed)} accounts: {', '.join(failed)}")
            print(f"{'='*80}")

        except FileNotFoundError:
            print(f"\n✗ Error: File not found: {filename}")
        except Exception as e:
            print(f"\n✗ Error executing unfollow list: {e}")

    def interactive_unfollow(self, inactive_users):
        """Main interactive unfollow workflow."""
        if not inactive_users:
            print("\n✓ No inactive users to unfollow!")
            return

        # Review and build unfollow list
        to_unfollow = self.interactive_review(inactive_users)

        if not to_unfollow:
            print("\n✗ No accounts marked for unfollowing")
            return

        # Summary
        print(f"\n{'='*80}")
        print(f"Summary: {len(to_unfollow)} accounts marked for unfollow")
        print(f"{'='*80}")
        for user in to_unfollow:
            print(f"  • @{user['username']} - {user['inactivity_reason']}")

        # Execute or save
        print(f"\n{'='*80}")
        print("What would you like to do?")
        print(f"{'='*80}")
        print("1. Execute unfollows NOW")
        print("2. Save to JSON file (review/edit later)")
        print("3. Cancel")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == '1':
            # Execute now
            confirm = input(f"\n⚠ Execute unfollows for {len(to_unfollow)} accounts? (yes/no): ").strip().lower()
            if confirm == 'yes':
                print("\n⏳ Executing unfollows...")
                success_count = 0
                for user in to_unfollow:
                    if self.unfollow_user(user['id'], user['username']):
                        success_count += 1
                print(f"\n✓ Successfully unfollowed {success_count}/{len(to_unfollow)} accounts")
            else:
                print("\n✗ Cancelled")
        elif choice == '2':
            # Save to file
            self.save_unfollow_list(to_unfollow)
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

  # Execute unfollows from a saved JSON file
  python twitter_unfollower.py --execute unfollow_list.json
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

    parser.add_argument(
        '--execute',
        type=str,
        metavar='FILE',
        help='Execute unfollows from a saved JSON file'
    )

    args = parser.parse_args()

    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          Twitter Unfollower CLI Tool                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    try:
        unfollower = TwitterUnfollower()

        # If --execute flag is provided, execute from file and exit
        if args.execute:
            unfollower.get_authenticated_user()
            unfollower.execute_unfollow_list(args.execute)
            return

        # Normal flow
        unfollower.get_authenticated_user()

        # Test API access level before proceeding
        unfollower.test_api_access()

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
