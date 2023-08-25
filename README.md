## Telegram Bot for adding the content of voice messages to an existing obsidian vault or other file collection via git.

# Requirements:
```
pyTelegramBotApi
whisper
python-dotenv
```

# Setup:

make a ".env" file in the bots directory with the following content:

```
TOKEN = "your telegram bot token"

REPO_PATH = "the repo you want to commit the files to"

```