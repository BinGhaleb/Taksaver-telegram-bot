#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

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
✅ ريديت (Reddit)
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
• الفيديوهات الطويلة جداً قد لا تعمل

❓ لتغيير اللغة استخدم: /language''',
        'processing': '⏳ جاري معالجة الرابط...',
        'downloading': '📥 جاري تحميل الفيديو...\n⏱️ قد يستغرق هذا بضع دقائق، الرجاء الانتظار...',
        'uploading': '📤 جاري رفع الفيديو إلى تيليجرام...\n⏱️ هذه الخطوة الأخيرة...',
        'success': '✅ تم التحميل بنجاح!',
        'error': '❌ حدث خطأ أثناء التحميل.\n\nالأسباب المحتملة:\n• الفيديو خاص أو محذوف\n• الرابط غير صحيح\n• الفيديو كبير جداً (أكثر من 50 ميجا)\n• الموقع يحتاج تسجيل دخول\n\nجرب رابط آخر أو تأكد من الرابط.',
        'invalid_url': '❌ الرابط غير صحيح!\nالرجاء إرسال رابط فيديو صحيح.',
        'too_large': '❌ حجم الفيديو كبير جداً!\nالحد الأقصى للحجم: 50 ميجابايت.\n\n💡 جرب فيديو أقصر أو ذو جودة أقل.',
        'subscribe_required': '⚠️ يجب عليك الاشتراك في القناة أولاً!\n\n👇 اشترك في القناة ثم اضغط "تحقق من الاشتراك"',
        'subscribe_button': '📢 اشترك في القناة',
        'check_subscription': '✅ تحقق من الاشتراك',
        'not_subscribed': '❌ لم تقم بالاشتراك بعد!\nالرجاء الاشتراك في القناة أولاً.',
        'language_changed': '✅ تم تغيير اللغة إلى العربية',
        'select_language': '🌍 اختر اللغة:',
        'processing_error': '❌ خطأ في معالجة الفيديو\nتفاصيل: {}',
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
✅ Reddit
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
• Very long videos may not work

❓ To change language use: /language''',
        'processing': '⏳ Processing link...',
        'downloading': '📥 Downloading video...\n⏱️ This may take a few minutes, please wait...',
        'uploading': '📤 Uploading video to Telegram...\n⏱️ Almost done...',
        'success': '✅ Download completed successfully!',
        'error': '❌ An error occurred during download.\n\nPossible reasons:\n• Video is private or deleted\n• Invalid link\n• Video is too large (over 50 MB)\n• Site requires login\n\nTry another link or check the URL.',
        'invalid_url': '❌ Invalid link!\nPlease send a valid video link.',
        'too_large': '❌ Video file is too large!\nMaximum size: 50 MB.\n\n💡 Try a shorter video or lower quality.',
        'subscribe_required': '⚠️ You must subscribe to the channel first!\n\n👇 Subscribe to the channel then click "Check Subscription"',
        'subscribe_button': '📢 Subscribe to Channel',
        'check_subscription': '✅ Check Subscription',
        'not_subscribed': '❌ You have not subscribed yet!\nPlease subscribe to the channel first.',
        'language_changed': '✅ Language changed to English',
        'select_language': '🌍 Select Language:',
        'processing_error': '❌ Error processing video\nDetails: {}',
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
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def get_ydl_opts(output_path: str):
    """إعدادات yt-dlp المحسّنة لجميع المواقع"""
    return {
        'format': 'best[filesize<50M][ext=mp4]/best[filesize<50M]/bestvideo[filesize<30M]+bestaudio[filesize<20M]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_color': True,
        'geo_bypass': True,
        'age_limit': None,
        # إعدادات خاصة بإنستغرام
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        # إعدادات لتحميل أفضل
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'keepvideo': False,
        'prefer_insecure': True,
        # تحويل إلى MP4 إذا لزم الأمر
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'merge_output_format': 'mp4',
        # إعدادات إضافية للمواقع المختلفة
        'cookiefile': None,
        'extractor_args': {
            'instagram': {
                'api_url': 'https://i.instagram.com/api/v1'
            }
        }
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    user_id = update.effective_user.id
    
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
    
    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_languages[user_id] = lang
        await query.edit_message_text(get_text(user_id, 'language_changed'))
        
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
    
    if not is_valid_url(url):
        await update.message.reply_text(get_text(user_id, 'invalid_url'))
        return
    
    processing_msg = await update.message.reply_text(get_text(user_id, 'processing'))
    
    filename = None
    try:
        # إنشاء مجلد tmp إذا لم يكن موجوداً
        os.makedirs('/tmp', exist_ok=True)
        
        # مسار الملف
        output_template = f'/tmp/video_{user_id}_%(id)s.%(ext)s'
        
        ydl_opts = get_ydl_opts(output_template)
        
        await processing_msg.edit_text(get_text(user_id, 'downloading'))
        
        # تحميل الفيديو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading from: {url}")
            info = ydl.extract_info(url, download=True)
            
            # الحصول على اسم الملف
            filename = ydl.prepare_filename(info)
            
            # في حالة التحويل إلى mp4
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + '.mp4'
            
            if not os.path.exists(filename):
                # البحث عن أي ملف تم تحميله
                import glob
                pattern = f'/tmp/video_{user_id}_*.*'
                files = glob.glob(pattern)
                if files:
                    filename = files[0]
                else:
                    raise Exception("File not found after download")
            
            title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
        logger.info(f"Downloaded to: {filename}")
        
        # التحقق من وجود الملف
        if not os.path.exists(filename):
            raise Exception(f"Downloaded file not found: {filename}")
        
        # التحقق من حجم الملف
        file_size = os.path.getsize(filename)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size > 50 * 1024 * 1024:  # 50 MB
            os.remove(filename)
            await processing_msg.edit_text(get_text(user_id, 'too_large'))
            return
        
        if file_size == 0:
            raise Exception("Downloaded file is empty")
        
        await processing_msg.edit_text(get_text(user_id, 'uploading'))
        
        # رفع الفيديو
        with open(filename, 'rb') as video_file:
            caption = f"🎬 {title}\n\n{get_text(user_id, 'success')}\n\n📢 {CHANNEL_LINK}"
            if len(caption) > 1024:
                caption = f"🎬 {title[:100]}...\n\n{get_text(user_id, 'success')}\n\n📢 {CHANNEL_LINK}"
            
            await update.message.reply_video(
                video=video_file,
                caption=caption,
                supports_streaming=True,
                width=info.get('width', 640),
                height=info.get('height', 360),
                duration=int(duration) if duration else None
            )
        
        # حذف الملف
        os.remove(filename)
        await processing_msg.delete()
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error downloading video from {url}: {error_msg}")
        
        # تنظيف الملف في حالة الخطأ
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
        
        # رسالة خطأ مفصلة
        try:
            await processing_msg.edit_text(get_text(user_id, 'error'))
        except:
            await update.message.reply_text(get_text(user_id, 'error'))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء"""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """بدء البوت"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
