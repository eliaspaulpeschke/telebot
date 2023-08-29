import dotenv
import telebot
import requests
import os
import time
from botstate import Botstate


state = Botstate()
token = dotenv.get_key("./.env", "TOKEN")
bot = telebot.TeleBot(token, parse_mode=None)



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
/keepspeech [on|off]
    works like datemode
    but for keeping voice
    messages as mp3
    with a timestamp
    - theyre still 
    also transcribed
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
            state.file = time.strftime("%d_%m_%y_%H_%M.md")
        elif (message.text == "/name today" or message.text == "/name daily"):
            state.file = time.strftime("%d_%m_%y.md")
        else:
            name = str(message.text)
            name = name.removeprefix("/name")
            name = name.strip()
            name = name.casefold()
            print(name)
            if (not name.isspace()) and (not name == ""):
                name = name.replace(" ", "_")
                state.file = name + ".md"
            else:
                bot.reply_to(message, "Please give a filename - syntax:\n /name <filename>")
        bot.reply_to(message, f"Current file name: {state.file}")


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
        res = requests.get(url, allow_redirects=True)
        with open("res.ogg", "wb") as f:
            f.write(res.content)
        os.system("ffmpeg -y -i res.ogg -ar 16000 -ac 1 -c:a pcm_s16le res.wav")
        os.system("/home/pi/whisper.cpp/main -m /home/pi/whisper.cpp/models/ggml-small-q5.bin -l auto -otxt -of res res.wav")
        with open("res.txt", "r") as txt:
            text = state.handleText("\n".join(txt.readlines()))
        save_text(text)
        if state.keepspeech:
            filename = time.strftime("%d-%m-%y-%H-%M-") + str(time.time()).replace(".", "_") + ".mp3"
            os.system(f"ffmpeg -y -i res.ogg {filename}")
        os.system("rm res.wav")
        bot.reply_to(message, f"Flename: {state.file}\n\n{text}")


@bot.message_handler(content_types=['text'], commands=['save'])
def handle_save(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/save")
        text = state.handleText(text)
        save_text(text)
        bot.reply_to(message, f"Appended your text to {state.file}")


@bot.message_handler(commands=["datemode", "keepspeech"])
def handle_flag(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.split(" ")
        cmd = text[0]
        if len(text) > 1:
            rest = text[1]
        else:
            rest = ""
        attrib = cmd.strip().removeprefix("/")
        if rest.strip() == "on":
            val = True
        elif rest.strip() == "off":
            val = False
        else:
            val = not state.__getattribute__(attrib)
        state.__setattr__(attrib, val)
        bot.reply_to(message, f"{attrib} set to {'on' if val else 'off'}")
    
@bot.message_handler(commands=['ls'])
def handle_ls(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
       files = os.listdir(state.repo_path)
       files.sort()
       bot.reply_to(message, "Files in your Repo: \n\n" + "\n".join(files))
       
@bot.message_handler(content_types=['text'], commands=['note', "notes"])
def handle_note(message):
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
            filename  = state.file
        with open(filename, "a") as file:
            file.write(text)
        os.system("git add . && git commit -m 'update' && git push")
        os.chdir(cwd)

@bot.message_handler(content_types=['text'], commands=['mv'])
def handle_move(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        text = message.text.removeprefix("/mv")
        text = text.strip()
        override = False
        if text.endswith("!override"):
            override = True
        text = text.removesuffix("!override")
        cmds = text.split(" ")
        if not (len(cmds) == 2):
            bot.reply_to(message, f"Two many commands - Syntax: \n /mv relative/path/1 relative/path/2")
            return
        if not (allowed_path(cmds[0]) and  allowed_path(cmds[1])):
            bot.reply_to(message, f"Path {cmds[0]} {'is not allowed' if not allowed_path(cmds[0]) else 'is allowed'} \
                         \n Path {cmds[1]} {'is not allowed' if not allowed_path(cmds[1]) else 'is allowed'}")
            return
        if not (os.path.exists(state.repo_path + "/" + cmds[0])):
            bot.reply_to(message, f"Path {cmds[0]} does not exist")
            return
        if (os.path.exists(state.repo_path + "/" + cmds[1])) and not override:
            bot.reply_to(message, f"Path {cmds[1]} does exist. Append !override to the message to override it")
            return
        cwd = os.getcwd()
        os.chdir(state.repo_path)
        os.system("git pull")
        os.system(f"mv {cmds[0]} {cmds[1]}")
        os.system("git add . && git commit -m 'update' && git push")
        os.chdir(cwd)
        files = os.listdir(state.repo_path)
        files.sort()
        bot.reply_to(message, "Files in your Repo: \n\n" + "\n".join(files))

def allowed_path(path):
    global state
    forbidden = [";", "&", "|", ">", "<", "`", '"', "'", "$", "@", "%", "{", "}", "[", "]", "?", "^", "~", ",", "=", "´"]
    if any([(x in path) for x in forbidden]):
        return False
    if str(path).startswith("./") or str(path).startswith("..") or str(path).startswith("/"):
        return False
    return True
    
def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()
