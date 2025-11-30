#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import re

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# معلومات البوت
BOT_TOKEN = "431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk"
CHANNEL_USERNAME = "@android_4"
CHANNEL_LINK = "https://t.me/android_4"

# النصوص بالعربية والإنجليزية
TEXTS = {
    'ar': {
        'choose_language': '🌍 اختر لغتك / Choose Your Language',
        'welcome': '''🎬 مرحباً بك في بوت تحميل الفيديوهات!

📥 أرسل لي رابط الفيديو من أي موقع وسأقوم بتحميله لك.

المواقع المدعومة:
✅ يوتيوب (YouTube)
✅ فيسبوك (Facebook)
✅ إنستغرام (Instagram)
✅ تيك توك (TikTok)
✅ تويتر/X (Twitter)
✅ فيميو (Vimeo)
✅ أكثر من 1000 موقع آخر!

⚙️ الأوامر المتاحة:
/start - بدء البوت
/language - تغيير اللغة
/help - المساعدة''',
        'help': '''📖 كيفية استخدام البوت:

1️⃣ أرسل رابط الفيديو
2️⃣ انتظر قليلاً أثناء التحميل
3️⃣ استلم الفيديو!

💡 نصائح:
• يمكنك إرسال عدة روابط
• تأكد من أن الرابط صحيح
• بعض المواقع قد تستغرق وقتاً أطول

❓ لتغيير اللغة استخدم: /language''',
        'processing': '⏳ جاري معالجة الرابط...',
        'downloading': '📥 جاري تحميل الفيديو...\nالرجاء الانتظار...',
        'uploading': '📤 جاري رفع الفيديو...',
        'success': '✅ تم التحميل بنجاح!',
        'error': '❌ حدث خطأ أثناء التحميل.\nتأكد من صحة الرابط وحاول مرة أخرى.',
        'invalid_url': '❌ الرابط غير صحيح!\nالرجاء إرسال رابط فيديو صحيح.',
        'too_large': '❌ حجم الفيديو كبير جداً!\nالحد الأقصى للحجم: 50 ميجابايت.',
        'subscribe_required': '⚠️ يجب عليك الاشتراك في القناة أولاً!\n\n👇 اشترك في القناة ثم اضغط "تحقق من الاشتراك"',
        'subscribe_button': '📢 اشترك في القناة',
        'check_subscription': '✅ تحقق من الاشتراك',
        'not_subscribed': '❌ لم تقم بالاشتراك بعد!\nالرجاء الاشتراك في القناة أولاً.',
        'language_changed': '✅ تم تغيير اللغة إلى العربية',
        'select_language': '🌍 اختر اللغة:',
    },
    'en': {
        'choose_language': '🌍 Choose Your Language / اختر لغتك',
        'welcome': '''🎬 Welcome to Video Downloader Bot!

📥 Send me a video link from any website and I'll download it for you.

Supported Sites:
✅ YouTube
✅ Facebook
✅ Instagram
✅ TikTok
✅ Twitter/X
✅ Vimeo
✅ More than 1000+ other sites!

⚙️ Available Commands:
/start - Start the bot
/language - Change language
/help - Help''',
        'help': '''📖 How to use the bot:

1️⃣ Send a video link
2️⃣ Wait while downloading
3️⃣ Receive your video!

💡 Tips:
• You can send multiple links
• Make sure the link is correct
• Some sites may take longer

❓ To change language use: /language''',
        'processing': '⏳ Processing link...',
        'downloading': '📥 Downloading video...\nPlease wait...',
        'uploading': '📤 Uploading video...',
        'success': '✅ Download completed successfully!',
        'error': '❌ An error occurred during download.\nCheck the link and try again.',
        'invalid_url': '❌ Invalid link!\nPlease send a valid video link.',
        'too_large': '❌ Video file is too large!\nMaximum size: 50 MB.',
        'subscribe_required': '⚠️ You must subscribe to the channel first!\n\n👇 Subscribe to the channel then click "Check Subscription"',
        'subscribe_button': '📢 Subscribe to Channel',
        'check_subscription': '✅ Check Subscription',
        'not_subscribed': '❌ You have not subscribed yet!\nPlease subscribe to the channel first.',
        'language_changed': '✅ Language changed to English',
        'select_language': '🌍 Select Language:',
    }
}

# تخزين اللغة المفضلة للمستخدمين
user_languages = {}

def get_text(user_id, key):
    """الحصول على النص المناسب حسب لغة المستخدم"""
    lang = user_languages.get(user_id, 'ar')
    return TEXTS[lang].get(key, TEXTS['ar'][key])

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق من اشتراك المستخدم في القناة"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

def is_valid_url(url: str) -> bool:
    """التحقق من صحة الرابط"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    user_id = update.effective_user.id
    
    # إذا لم يختر المستخدم لغة بعد، اعرض خيارات اللغة
    if user_id not in user_languages:
        keyboard = [
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            TEXTS['ar']['choose_language'],
            reply_markup=reply_markup
        )
        return
    
    # التحقق من الاشتراك
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton(get_text(user_id, 'subscribe_button'), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text(user_id, 'check_subscription'), callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            get_text(user_id, 'subscribe_required'),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(get_text(user_id, 'welcome'))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    user_id = update.effective_user.id
    await update.message.reply_text(get_text(user_id, 'help'))

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /language"""
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_id = update.effective_user.id
    await update.message.reply_text(
        get_text(user_id, 'select_language'),
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أزرار الكيبورد"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # معالجة تغيير اللغة
    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_languages[user_id] = lang
        await query.edit_message_text(get_text(user_id, 'language_changed'))
        
        # إرسال رسالة الترحيب بعد اختيار اللغة
        is_subscribed = await check_subscription(user_id, context)
        if not is_subscribed:
            keyboard = [
                [InlineKeyboardButton(get_text(user_id, 'subscribe_button'), url=CHANNEL_LINK)],
                [InlineKeyboardButton(get_text(user_id, 'check_subscription'), callback_data="check_sub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text(user_id, 'subscribe_required'),
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text(user_id, 'welcome')
            )
    
    # معالجة التحقق من الاشتراك
    elif query.data == "check_sub":
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await query.edit_message_text(get_text(user_id, 'welcome'))
        else:
            await query.answer(get_text(user_id, 'not_subscribed'), show_alert=True)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تحميل الفيديو من الرابط"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    # التحقق من اختيار اللغة
    if user_id not in user_languages:
        keyboard = [
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            TEXTS['ar']['choose_language'],
            reply_markup=reply_markup
        )
        return
    
    # التحقق من الاشتراك
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton(get_text(user_id, 'subscribe_button'), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text(user_id, 'check_subscription'), callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            get_text(user_id, 'subscribe_required'),
            reply_markup=reply_markup
        )
        return
    
    # التحقق من صحة الرابط
    if not is_valid_url(url):
        await update.message.reply_text(get_text(user_id, 'invalid_url'))
        return
    
    # إرسال رسالة المعالجة
    processing_msg = await update.message.reply_text(get_text(user_id, 'processing'))
    
    try:
        # إعدادات yt-dlp
        ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': f'/tmp/%(title)s_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # تحديث رسالة التحميل
        await processing_msg.edit_text(get_text(user_id, 'downloading'))
        
        # تحميل الفيديو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'video')
        
        # التحقق من حجم الملف
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:  # 50 MB
            os.remove(filename)
            await processing_msg.edit_text(get_text(user_id, 'too_large'))
            return
        
        # تحديث رسالة الرفع
        await processing_msg.edit_text(get_text(user_id, 'uploading'))
        
        # رفع الفيديو
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"🎬 {title}\n\n{get_text(user_id, 'success')}\n\n📢 {CHANNEL_LINK}",
                supports_streaming=True
            )
        
        # حذف الملف
        os.remove(filename)
        
        # حذف رسالة المعالجة
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await processing_msg.edit_text(get_text(user_id, 'error'))
        
        # حذف الملف في حالة الخطأ
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء"""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """بدء البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
