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
/name [now|today|daily]
    sets the files
    name to the current
    date and time
    or only date for latter two
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
/mv relative/path/1 relative/path/2 [!override]
    moves path1 to path2
    overrides when override flag is set
/save
    appends message to
    the selected file
/note
    appends message to
    notes.md
/daily
    appends message to
    dd_mm_yy.md
    

all
voice messages are
transcribed to your
file.
""")
                 
@bot.message_handler(commands=["name"])
def change_name(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        if (message.text == "/name now"):
            state.setfile(time.strftime("%d_%m_%y_%H_%M.md"))
        elif (message.text == "/name today" or message.text == "/name daily"):
            state.setfile(time.strftime("%d_%m_%y.md"))
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
        elif(message.text == "/datemode on"):
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
       
@bot.message_handler(content_types=['text'], commands=['note', "notes"])
def handle_save(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/notes")
        text = text.removeprefix("/note")
        if state.datemode == False:
            text = time.strftime("\n%d.%m.%y - %H:%M:\n") + text
        text = state.handleText(text)
        save_text(text, "notes.md")
        bot.reply_to(message, f"Added to notes.md")
        
@bot.message_handler(content_types=['text'], commands=['daily'])
def handle_save(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/daily")
        if state.datemode == False:
            text = time.strftime("\n%H:%M\n") + text
        text = state.handleText(text)
        save_text(text, time.strftime("%d_%m_%y.md"))
        bot.reply_to(message, f"Added to {time.strftime('%d_%m_%y.md')}")

def save_text(text, filename=None):
        global state
        cwd = os.getcwd()
        os.chdir(state.repo_path)
        os.system("git pull")
        if (filename == None):
            filename  = state.currentfile
        with open(filename, "a") as file:
            file.write(text)
        os.system("git add . && git commit -m 'update' && git push")
        os.chdir(cwd)

@bot.message_handler(content_types=['text'], commands=['mv'])
def handle_save(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/mv")
        text = text.strip()
        override = False
        if text.endswith("!override"):
            override = True
        text = text.removesuffix("!override")
        cmds = text.split(" ")
        if (len(cmds) == 2):
            if allowed_path(cmds[0]) and  allowed_path(cmds[1]):
                if os.path.exists(state.repo_path + "/" + cmds[0]):
                    if (not os.path.exists(state.repo_path + "/" + cmds[1])) or override:
                        cwd = os.getcwd()
                        os.chdir(state.repo_path)
                        os.system("git pull")
                        os.system(f"mv {cmds[0]} {cmds[1]}")
                        os.system("git add . && git commit -m 'update' && git push")
                        os.chdir(cwd)
                        files = os.listdir(state.repo_path)
                        files.sort()
                        bot.reply_to(message, "Files in your Repo: \n\n" + "\n".join(files))
                    else:
                        bot.reply_to(message, f"Path {cmds[1]} does exist. Append !override to the message to override it")
                else:
                    bot.reply_to(message, f"Path {cmds[0]} does not exist")
            else:
                bot.reply_to(message, f"Path {cmds[0]} {'is not allowed' if not allowed_path(cmds[0]) else 'is allowed'} \n Path {cmds[1]} {'is not allowed' if not allowed_path(cmds[1]) else 'is allowed'}")
        else:
            bot.reply_to(message, f"Two many commands - Syntax: \n /mv relative/path/1 relative/path/2")
           

def allowed_path(path):
    global state
    if (";" in path) or ("&&" in path) or ("&" in path) or ("|" in path) or ("||" in path) or (">" in path) or ("<" in path):
        return False
    if str(path).startswith("./") or str(path).startswith("..") or str(path).startswith("/"):
        return False
    return True
    
def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()