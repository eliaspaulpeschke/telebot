import dotenv
import telebot
import requests
import whisper



token = dotenv.get_key("./.env", "TOKEN")
bot = telebot.TeleBot(token, parse_mode=None)
model = whisper.load_model("base")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")
	
@bot.message_handler(content_types=["voice"])
def echo_all(message):
    print(message.voice.file_id)
    url = bot.get_file_url(message.voice.file_id)
    f = requests.get(url, allow_redirects=True)
    with open("res.ogg", "wb") as file:
        file.write(f.content)
    result = model.transcribe("res.ogg")
    print(result["text"].replace(" Fragezeichen ", "? ").replace(" Komma ", ", ").replace(" Punkt ", ". "))

bot.infinity_polling()