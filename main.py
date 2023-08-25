import dotenv
import telebot
import requests
import whisper
import os
import time
from botstate import Botstate


state = Botstate()
token = dotenv.get_key("./.env", "TOKEN")
bot = telebot.TeleBot(token, parse_mode=None)
model = whisper.load_model("base")

known_commands = ["Command Link", "Command Help"]



@bot.message_handler(commands=["start", "help"])
def help(message):
    bot.reply_to(message, """
Known Commands:
                 
/name <filename>
    set name of 
    current file 
    to append to
/name [now|today]
    sets the files
    name to the current
    date and time
/id 
    check authorization
/datemode [on|off]
    prepending current
    time and date
    to content
    (without on/off
    just toggles)  
/ls
    list all files
/save
    appends message to
    the selected file

all
voice messages are
transcribed to your
file.
""")
                 
@bot.message_handler(commands=["name"])
def change_name(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        if (message.text == "/name now" or message.text == "/name today"):
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
def handle_id(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        bot.reply_to(message, "You are an authorized user.")
    else:
        bot.reply_to(message, f"Invalid, your ID is {message.from_user.id}. If you're an admin, add it to ALLOWED_USERIDS in your .env-file.")

        
@bot.message_handler(content_types=["voice"])
def handle_voicemsg(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        print(message.voice.file_id)
        url = bot.get_file_url(message.voice.file_id)
        f = requests.get(url, allow_redirects=True)
        with open("res.ogg", "wb") as file:
            file.write(f.content)
        result = model.transcribe("res.ogg")
        text = state.handleText(result["text"])
        save_text(text)
        bot.reply_to(message, f"Flename: {state.currentfile}\n\n{text}")


@bot.message_handler(content_types=['text'], commands=['save'])
def handle_save(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/save")
        text = state.handleText(text)
        save_text(text)
        bot.reply_to(message, f"Appendedd your text to {state.currentfile}")
    
@bot.message_handler(commands=['datemode'])
def handle_date(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        if(message.text == "/datemode"):
            state.setdatemode(not state.datemode)
        elif(message.text == "/datemode off"):
            state.setdatemode(False)
        elif(message.text == "/datemode off"):
            state.setdatemode(True)
        else:
            bot.reply_to(message, "Usage: \n /datemode - toggle \n /datemode on - turn on \n /datemode off - turn off")
        bot.reply_to(message, f"Datemode is {'on' if state.datemode == True else 'off'}")
    
@bot.message_handler(commands=['ls'])
def handle_ls(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
       files = os.listdir(state.repo_path)
       files.sort()
       bot.reply_to(message, "Files in your Repo: \n\n" + "\n".join(files))

def save_text(text):
        global state
        cwd = os.getcwd()
        os.chdir(state.repo_path)
        os.system("git pull")
        with open(state.currentfile, "a") as file:
            file.write(text)
        os.system("git add . && git commit -m 'update' && git push")
        os.chdir(cwd)
    
def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()