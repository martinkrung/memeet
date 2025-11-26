# Twitter Unfollower CLI Tool

A Python command-line tool to help you unfollow inactive Twitter accounts based on their last tweet date.

## Features

- ✨ **Configurable Inactivity Period**: Set any custom time period (default: 2 years)
- 💾 **Smart Caching**: Cache follower data to avoid re-fetching from Twitter API
- 🎯 **Interactive Unfollowing**: Choose to unfollow all at once or review one by one
- 📊 **Detailed Stats**: See each account's last tweet date and inactivity period
- 🔒 **Rate Limit Handling**: Automatically waits when hitting Twitter API limits
- 🚀 **Fast**: Uses Twitter API v2 for optimal performance

## Prerequisites

- Python 3.7 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Twitter Developer Account with API access
- Twitter API credentials (API Key, API Secret, Access Token, Access Token Secret, Bearer Token)

## Installation

1. **Install uv** (if not already installed):
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Or via pip
   pip install uv
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd memeet
   ```

3. **Install dependencies with uv**:
   ```bash
   uv pip install -r requirements.txt
   ```

   Or if you want uv to manage the virtual environment automatically:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

4. **Set up Twitter API credentials**:

   > **IMPORTANT**: Your app must be attached to a Project in the Twitter Developer Portal to use API v2.

   a. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)

   b. **Create a Project** (required for API v2):
      - Click "Projects & Apps" in the left sidebar
      - Click "+ Create Project" (or use an existing project)
      - Give it a name (e.g., "Twitter Unfollower")
      - Select use case and fill in the required details
      - Click "Next" until complete

   c. **Create or Add an App to your Project**:
      - Inside your project, click "+ Add App" or "Create new app"
      - Give your app a name (e.g., "Unfollower CLI")
      - Save the API Key and API Secret that appear (you'll need these!)

   d. **Configure App Permissions**:
      - Go to your app's settings (click the gear icon next to your app name)
      - Click "User authentication settings" → "Set up"
      - Enable "OAuth 1.0a"
      - Set App permissions to **"Read and write"** (required to unfollow)
      - Fill in required fields (you can use `http://localhost:3000` for callback URL if needed)
      - Click "Save"

   e. **Generate Access Tokens**:
      - Go to the "Keys and tokens" tab for your app
      - Under "Authentication Tokens", click "Generate" for Access Token and Secret
      - **IMPORTANT**: Save these immediately - you won't see them again!
      - You should now have:
        - API Key (Consumer Key)
        - API Secret (Consumer Secret)
        - Access Token
        - Access Token Secret
        - Bearer Token (shown at top of page)

   f. **Copy credentials to .env**:
      ```bash
      cp .env.example .env
      ```

   g. **Edit `.env` and add your credentials**:
      ```
      TWITTER_API_KEY=your_api_key_here
      TWITTER_API_SECRET=your_api_secret_here
      TWITTER_ACCESS_TOKEN=your_access_token_here
      TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
      TWITTER_BEARER_TOKEN=your_bearer_token_here
      ```

      > **Note**: Remove any quotes or extra spaces around the values

## Usage

### Basic Usage

Find accounts that haven't tweeted in 2 years (730 days):
```bash
# If using uv-managed venv
python twitter_unfollower.py

# Or run directly with uv
uv run twitter_unfollower.py
```

### Custom Inactivity Period

Find accounts inactive for 1 year (365 days):
```bash
python twitter_unfollower.py --days 365
```

Find accounts inactive for 6 months (180 days):
```bash
python twitter_unfollower.py --days 180
```

Find accounts inactive for 3 years:
```bash
python twitter_unfollower.py --days 1095
```

### Force Refresh Data

Ignore cached data and fetch fresh data from Twitter:
```bash
python twitter_unfollower.py --days 730 --refresh
```

### List Only Mode

Just see the list without unfollowing anyone:
```bash
python twitter_unfollower.py --days 730 --list-only
```

## How It Works

1. **Authentication**: The tool authenticates with Twitter using your API credentials

2. **Fetch Following**: Retrieves all accounts you follow (cached for efficiency)

3. **Check Activity**: For each account, checks their last original tweet date
   - Excludes retweets and replies
   - Only counts original tweets

4. **Filter Inactive**: Identifies accounts that haven't tweeted in the specified period

5. **Display Results**: Shows you a list of all inactive accounts with details

6. **Interactive Unfollowing**: Gives you two options:
   - **Unfollow all at once**: Bulk unfollow with confirmation
   - **Unfollow one by one**: Review each account and decide individually

## Caching

The tool creates a `followers_cache.json` file to store follower data. This prevents having to re-fetch all data every time you run the tool.

**Cache benefits**:
- Faster subsequent runs
- Reduces API calls
- Preserves data if you want to try different inactivity periods

**When to refresh cache**:
- You've followed/unfollowed accounts since last run
- You want the most up-to-date data
- Use the `--refresh` flag

## Command-Line Options

```
usage: twitter_unfollower.py [-h] [--days DAYS] [--refresh] [--list-only]

Twitter Unfollower CLI - Unfollow inactive accounts

optional arguments:
  -h, --help   show this help message and exit
  --days DAYS  Number of days of inactivity to consider (default: 730 = 2 years)
  --refresh    Force refresh data from Twitter (ignore cache)
  --list-only  Only list inactive accounts without unfollowing
```

## Example Session

```
╔═══════════════════════════════════════════════════════════════╗
║          Twitter Unfollower CLI Tool                         ║
╚═══════════════════════════════════════════════════════════════╝

✓ Authenticated as: @yourusername

✓ Loaded cached data from followers_cache.json
  Cache created: 2025-11-26T10:30:00+00:00

⏳ Analyzing accounts for 730 days (2 years) of inactivity...

================================================================================
Found 42 inactive accounts:
================================================================================

1. @oldaccount1 (Old Account Name)
   └─ Last tweet 892 days ago
   └─ Last tweet: 2023-06-15T14:23:00+00:00

2. @abandoneduser (Abandoned User)
   └─ No original tweets found

...

================================================================================
Unfollow Options:
================================================================================
1. Unfollow all at once
2. Unfollow one by one (ask for each)
3. Cancel

Enter your choice (1-3): 2

⏳ Starting one-by-one unfollowing...

[1/42] @oldaccount1 (Old Account Name)
   Last tweet 892 days ago
   Unfollow? (y/n/q to quit): y
   ✓ Unfollowed @oldaccount1

[2/42] @abandoneduser (Abandoned User)
   No original tweets found
   Unfollow? (y/n/q to quit): n
   ↷ Skipped

...
```

## Troubleshooting

### "403 Forbidden" or "App must be attached to a Project" error

This is the most common error! It means your Twitter app is not properly set up:

**Solution**:
1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Click "Projects & Apps" in the sidebar
3. **Create a Project** if you don't have one
4. **Add your app to the project** (or create a new app inside the project)
5. **Important**: After adding the app to a project, you MUST regenerate your Access Token and Secret
6. Go to "Keys and tokens" → Regenerate "Access Token and Secret"
7. Update your `.env` file with the new tokens
8. Also verify that App permissions are set to "Read and write"

### "Missing Twitter API credentials" error

Make sure you have:
1. Created a `.env` file (copy from `.env.example`)
2. Added all required credentials to the `.env` file
3. No extra spaces or quotes around the values

### Rate Limit Errors

The tool automatically handles rate limits by waiting when needed. However, if you have many followers (10,000+), the initial data fetch may take a while.

### "Could not fetch tweets" warnings

Some accounts may have:
- Protected tweets (you can't see them)
- No original tweets (only retweets/replies)
- Been suspended or deleted

These accounts will be marked as "No original tweets found" in the inactive list.

## Safety Features

- **Confirmation required**: For bulk unfollowing, you must type "yes" to confirm
- **One-by-one option**: Review each account before unfollowing
- **List-only mode**: Preview results without making any changes
- **Cached data**: Your data is saved locally, no need to re-fetch

## API Rate Limits

Twitter API has the following limits (per 15-minute window):
- **Get following**: 15 requests (1000 users per request)
- **Get user tweets**: 900 requests
- **Destroy friendship**: 50 requests

The tool automatically handles rate limits by waiting when necessary.

## Privacy & Security

- Your API credentials are stored locally in `.env` (never committed to git)
- The cache file is stored locally (never shared)
- No data is sent to any third-party services
- All operations use official Twitter API

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## Disclaimer

Use this tool responsibly. Mass unfollowing may trigger Twitter's automation detection. It's recommended to:
- Unfollow in batches (not thousands at once)
- Use reasonable inactivity periods
- Take breaks between batches

This tool is for personal use only. The author is not responsible for any account restrictions or bans resulting from its use.
