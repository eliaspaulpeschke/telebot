## Telegram Bot for adding the content of voice messages to an existing obsidian vault or other file collection via git.

# Requirements:
```
pyTelegramBotApi
python-dotenv
```

installed [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - model and binary are determined in .env

# Setup:

make a ".env" file in the bots directory with the following content:

```
TOKEN = "your telegram bot token"

REPO_PATH = "the repo you want to commit the files to"

DATA_STORAGE="./data.pickle" #Or any path you like

ALLOWED_USERIDS="<your telegram ID here>"  #Send /id to the bot to find out your ID and check that authentication works

WHISPER_MODEL = "/home/user/whisper.cpp/models/ggml_base.en.bin"

WHISPER_PATH = "/home/user/whisper.cpp/main"

```