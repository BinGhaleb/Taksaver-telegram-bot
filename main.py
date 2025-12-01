import telebot
from telebot import types
import yt_dlp
import os

# Configuration
TOKEN = '431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk'
CHANNEL_USERNAME = '@android_4' # Channel to check subscription

bot = telebot.TeleBot(TOKEN)
user_languages = {}

# Phrases
STRINGS = {
    'ar': {
        'welcome': 'أهلاً بك! يرجى اختيار لغتك:',
        'sub_error': f'عذراً، يجب عليك الاشتراك في القناة أولاً: {CHANNEL_USERNAME}',
        'send_link': 'أرسل لي رابط الفيديو لتحميله.',
        'downloading': 'جاري التحميل... ⏳',
        'error': 'حدث خطأ أثناء التحميل. تأكد من صحة الرابط.',
        'select_lang': 'تم اختيار العربية.'
    },
    'en': {
        'welcome': 'Welcome! Please select your language:',
        'sub_error': f'Sorry, you must subscribe to our channel first: {CHANNEL_USERNAME}',
        'send_link': 'Send me a video link to download.',
        'downloading': 'Downloading... ⏳',
        'error': 'Error downloading. Please check the link.',
        'select_lang': 'English selected.'
    }
}

def check_subscription(user_id):
    try:
        # Get chat member status
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        # Only allow these statuses
        return status in ['creator', 'administrator', 'member']
    except Exception as e:
        # If bot is not admin in channel, this will fail
        print(f"Error checking subscription: {e}")
        return False 

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_ar = types.InlineKeyboardButton("العربية 🇸🇦", callback_data='lang_ar')
    btn_en = types.InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')
    markup.add(btn_ar, btn_en)
    bot.send_message(message.chat.id, "Choose Language / اختر اللغة", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_language(call):
    lang = call.data.split('_')[1]
    user_languages[call.message.chat.id] = lang
    
    text = STRINGS[lang]['select_lang'] + "\n" + STRINGS[lang]['send_link']
    
    # Edit the message instead of sending a new one
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    user_id = message.chat.id
    
    # 1. Check Subscription Logic
    if not check_subscription(user_id):
        bot.send_message(user_id, f"Please subscribe to our channel first / يرجى الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")
        return

    # 2. Check Language Preference
    lang = user_languages.get(user_id, 'ar') # Default to Arabic if not set
    
    url = message.text
    # Simple URL validation
    if not url.startswith('http'):
        bot.send_message(user_id, STRINGS[lang]['error'])
        return

    msg = bot.send_message(user_id, STRINGS[lang]['downloading'])

    # 3. Download Logic using yt-dlp
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'max_filesize': 50 * 1024 * 1024,  # 50MB limit (Telegram Bot API limit)
            'quiet': True
        }
        
        filename = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Send the video
        with open(filename, 'rb') as video:
            bot.send_video(user_id, video, caption="@dfcbot", reply_to_message_id=message.message_id)
        
        # Cleanup: remove file from server
        if os.path.exists(filename):
            os.remove(filename)
            
        bot.delete_message(user_id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(STRINGS[lang]['error'], chat_id=user_id, message_id=msg.message_id)
        print(f"Download Error: {e}")

print("Bot is running...")
bot.infinity_polling()
