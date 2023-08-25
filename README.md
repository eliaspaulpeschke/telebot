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

DATA_STORAGE="./data.pickle" #Or any path you like

ALLOWED_USERIDS="<your telegram ID here>"  #Send /id to the bot to find out your ID and check that authentication works

```