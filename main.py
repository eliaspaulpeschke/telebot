import dotenv
import telebot
import requests
import whisper
import os
import time

currentfile = ""
token = dotenv.get_key("./.env", "TOKEN")
repo_path = dotenv.get_key("./.env", "REPO_PATH")
bot = telebot.TeleBot(token, parse_mode=None)
model = whisper.load_model("base")


@bot.message_handler(commands=['start', 'help', "name"])
def send_welcome(message):
    global currentfile
    bot.reply_to(message, "Howdy, how are you doing?")
    if message.text.startswith("/name"):
        name=str(message.text)
        name = name.removeprefix("/name")
        name = name.strip()
        name = name.replace(" ", "_")
        name = name.casefold()
        currentfile = name + ".md"
        bot.reply_to(message, currentfile)
        
@bot.message_handler(content_types=["voice"])
def echo_all(message):
    print(message.voice.file_id)
    url = bot.get_file_url(message.voice.file_id)
    f = requests.get(url, allow_redirects=True)
    with open("res.ogg", "wb") as file:
        file.write(f.content)
    result = model.transcribe("res.ogg")
    cwd = os.getcwd()
    os.chdir(repo_path)
    os.system("git pull")
    with open(currentfile, "a") as file:
        file.write(time.strftime("\n%d.%m.%y - %H:%M:\n"))
        file.write(result["text"])
    os.system("git add . && git commit -m 'update' && git push")
    os.chdir(cwd)
    bot.reply_to(message, f"Flename: {currentfile}\n\n{result['text']}")

bot.infinity_polling()