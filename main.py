import dotenv
import telebot
import requests
import whisper
import os
import time
from botstate import Botstate


state = Botstate()
bot = telebot.TeleBot(state.token, parse_mode=None)
model = whisper.load_model("base")

known_commands = ["Command Link", "Command Help"]



@bot.message_handler(commands=["name"])
def send_welcome(message):
    global state
    if (message.text == ("/name now")):
        state.setfile(time.strftime("%d_%m_%y_%H_%M.md"))
    else:
        name = str(message.text)
        name = name.removeprefix("/name")
        name = name.strip()
        name = name.casefold()
        print(name)
        if (not name.isspace()) and (not name == ""):
            name = name.replace(" ", "_")
            state.setfile(name + ".md")
        else:
            bot.reply_to(message, "Please give a filename - syntax:\n /name <filename>")
    bot.reply_to(message, f"Current file name: {state.currentfile}")

@bot.message_handler(commands=['id'])
def send_welcome(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        bot.reply_to(message, "You are an authorized user.")
    else:
        bot.reply_to(message, f"Invalid, your ID is {message.from_user.id}. If you're an admin, add it to ALLOWED_USERIDS in your .env-file.")

        
@bot.message_handler(content_types=["voice"])
def echo_all(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        print(message.voice.file_id)
        url = bot.get_file_url(message.voice.file_id)
        f = requests.get(url, allow_redirects=True)
        with open("res.ogg", "wb") as file:
            file.write(f.content)
        result = model.transcribe("res.ogg")
        save_text(result["text"])
        bot.reply_to(message, f"Flename: {state.currentfile}\n\n{result['text']}")

def save_text(text):
        global state
        cwd = os.getcwd()
        os.chdir(state.repo_path)
        os.system("git pull")
        with open(state.currentfile, "a") as file:
            file.write(time.strftime("\n%d.%m.%y - %H:%M:\n"))
            file.write(text)
        os.system("git add . && git commit -m 'update' && git push")
        os.chdir(cwd)
    




def main():
    global currentfile
    

    bot.infinity_polling()

if __name__ == "__main__":
    main()