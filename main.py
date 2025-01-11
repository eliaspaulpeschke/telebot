#!/usr/bin/env python3

import dotenv
import telebot
import requests
import os
from datetime import datetime 
from botstate import Botstate


state = Botstate()
dotenv.load_dotenv()
token = os.environ.get("TOKEN", "")
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
/lang de|en|it|fr|auto
    set language mode
    for audio transcription
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
/cat file
    prints file's content to telegram
/tail file n
    prints n last lines of file's content
/tail file n m
    prints lines n to m of file

all
voice messages are
transcribed to your
file.
""")

def check_user(message):
    global state
    if (str(message.from_user.id) in state.allowed_ids):
        return True
    return False

def process_text(text, add_date = False, override_datemode = False):
    if (state.datemode or add_date and not override_datemode):
        return f"\n {datetime.now().isoformat()}: " + text
    else:
        if not text.startswith("\n"): text = "\n" + text
        return text

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

def allowed_path(path):
    global state
    forbidden = [";", "&", "|", ">", "<", "`", '"', "'", "$", "@", "%", "{", "}", "[", "]", "?", "^", "~", ",", "=", "´"]
    if any([(x in path) for x in forbidden]):
        return False
    if str(path).startswith("./") or str(path).startswith("..") or str(path).startswith("/"):
        return False
    return True

@bot.message_handler(commands=["name"])
def change_name(message):
    global state
    if not check_user(message): return
    if (message.text == "/name now"):
        state.file = time.strftime("%d_%m_%y_%H_%M.md")
    elif (message.text == "/name today" or message.text == "/name daily"):
        state.file = time.strftime("%d_%m_%y.md")
    else:
        name = str(message.text)
        name = name.removeprefix("/name")
        name = name.strip()
        name = name.casefold()
        if (not name.isspace()) and (not name == ""):
            name = name.replace(" ", "_")
            state.file = name + ".md"
        else:
            bot.reply_to(message, "Please give a filename - syntax:\n /name <filename>")
    bot.reply_to(message, f"Current file name: {state.file}")


@bot.message_handler(commands=['id'])
def handle_id(message):
    global state
    if check_user(message):
        bot.reply_to(message, "You are an authorized user.")
    else:
        bot.reply_to(message, f"Invalid, your ID is {message.from_user.id}. If you're an admin, add it to ALLOWED_USERIDS in your .env-file.")
        

@bot.message_handler(content_types=["voice"])
def handle_voicemsg(message):
    global state
    if not check_user(message): return
    url = bot.get_file_url(message.voice.file_id)
    res = requests.get(url, allow_redirects=True)
    with open("res.ogg", "wb") as f:
        f.write(res.content)
    os.system("ffmpeg -y -i res.ogg -ar 16000 -ac 1 -c:a pcm_s16le res.wav")
    os.system(f"{state.whisper_path} -m {state.whisper_model} -l {state.lang} -otxt -of res res.wav")
    with open("res.txt", "r") as txt:
        text = process_text("\n".join(txt.readlines()))
    save_text(text)
    if state.keepspeech:
        filename = time.strftime("%d-%m-%y-%H-%M-") + str(time.time()).replace(".", "_") + ".mp3"
        os.system(f"ffmpeg -y -i res.ogg {filename}")
    os.system("rm res.wav")
    bot.reply_to(message, f"Flename: {state.file}\n\n{text}")


@bot.message_handler(content_types=['text'], commands=['save'])
def handle_save(message):
    global state
    if not check_user(message): return
    text = message.text.removeprefix("/save")
    text = process_text(text)
    save_text(text)
    bot.reply_to(message, f"Appended your text to {state.file}")


@bot.message_handler(commands=["datemode", "keepspeech", "lang"])
def handle_flag(message):
    global state
    if not check_user(message): return
    text = message.text.split(" ")
    cmd = text[0]
    if len(text) > 1:
        rest = text[1]
    else:
        rest = ""
    #print(message, "\n", cmd, "\n", rest, "\n\n", text)
    attrib = cmd.strip().removeprefix("/")
    if rest == "on":
        val = True
    elif rest == "off":
        val = False
    elif rest != "" and attrib == "lang":
        val = rest.strip()
        #print(val)
    elif not attrib == "lang":
        val = not state.__getattribute__(attrib)
    else:
        return
    state.__setattr__(attrib, val)
    bot.reply_to(message, f"{attrib} set to {state.__getattribute__(attrib) if type(val) == str else 'on' if val else 'off'}")


@bot.message_handler(commands=['ls'])
def handle_ls(message):
    global state
    if not check_user(message): return
    files = os.listdir(state.repo_path)
    files.sort()
    bot.reply_to(message, "Files in your Repo: \n\n" + "\n".join(files))
   
@bot.message_handler(content_types=['text'], commands=['note', "notes"])
def handle_note(message):
    global state
    if not check_user(message): return
    text = message.text.removeprefix("/notes")
    text = text.removeprefix("/note")
    text = process_text(text, add_date=True)
    save_text(text, "notes.md")
    bot.reply_to(message, f"Added to notes.md")
    
@bot.message_handler(content_types=['text'], commands=['daily'])
def handle_daily(message):
    global state
    if not check_user(message): return
    text = message.text.removeprefix("/daily")
    text = process_text(text, add_date=True)
    filename = datetime.now().strftime("%d_%m_%y.md")
    save_text(text, filename)
    bot.reply_to(message, f"Added to {filename}")

@bot.message_handler(content_types=['text'], commands=['mv'])
def handle_move(message):
    global state
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

def read_file(path, n = None, m = None):
    with open(path) as f:
        lines = f.readlines()
        if n is None and m is None:
            return "\n".join(lines)
        elif n is not None and m is None:
            return "\n".join(lines[-int(n):])
        elif n is not None and m is not None:
            return "\n".join(lines[int(n)-1:int(m)-1])
        else:
            return "\n".join(lines)

@bot.message_handler(content_types=['text'], commands=['cat'])
def handle_cat(message):
    global state
    if not check_user(message): return

    _, path = message.text.strip().split(" ")
    if not allowed_path(path):
        bot.reply_to(message, "Invalid path.")
        return
    bot.reply_to(message, read_file(os.path.join(state.repo_path, path)))

@bot.message_handler(content_types=['text'], commands=['tail'])
def handle_tail(message):
    global state
    if not check_user(message): return

    _, path, *nums = message.text.strip().split(" ")
    if not allowed_path(path):
        bot.reply_to(message, "Invalid path.")
        return
    if len(nums) == 0:
        bot.reply_to(message, read_file(os.path.join(state.repo_path, path), n=10))
    if len(nums) == 1:
        bot.reply_to(message, read_file(os.path.join(state.repo_path, path), n=nums[0]))
    if len(nums) == 2:
        bot.reply_to(message, read_file(os.path.join(state.repo_path, path), n=nums[0], m=nums[1]))

@bot.message_handler(func=lambda x: True)
def catchall(message):
    if message.text.startswith("/"): return
    handle_save(message)
    
def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()
