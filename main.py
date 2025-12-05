import logging
import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ChatMemberStatus
from yt_dlp import YoutubeDL

# ----------------------------------------------------------------------
# 1. إعدادات البوت والتوكن والقناة
# التوكن: 431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk
BOT_TOKEN = "431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk"
# ID القناة الرقمي (المُصحح): -1001490999062
REQUIRED_CHANNEL_ID = -1001490999062
CHANNEL_LINK = "https://t.me/Typo2020"

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 2. دالة التحقق من الاشتراك في القناة
async def check_subscription(user_id: int, bot: Bot) -> bool:
    """يتحقق مما إذا كان المستخدم مشتركًا في القناة المطلوبة."""
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        # يُعتبر المستخدم مشتركاً إذا كانت حالته ليست "مغادر" أو "محظور"
        is_subscribed = member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED)
        return is_subscribed
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        # إذا حدث خطأ (عادةً بسبب عدم وجود صلاحيات كافية للبوت في القناة)، نفشل التحقق
        return False

# ----------------------------------------------------------------------
# 3. دالة معالج أمر /start
async def start_command(update: Update, context) -> None:
    """يرد على أمر /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً بك يا {user.mention_html()}!\n\n"
        "أنا بوت التحميل. أرسل لي رابط أي فيديو/ملف وسأقوم بتحميله."
    )

# ----------------------------------------------------------------------
# 4. دالة معالج رسائل الروابط (Downloader)
async def handle_link(update: Update, context) -> None:
    """يستقبل الرابط ويقوم بمعالجته وتحميله."""
    user_id = update.effective_user.id
    bot = context.bot
    message_text = update.message.text
    
    # 4.1 التحقق من الاشتراك
    if not await check_subscription(user_id, bot):
        # رسالة عدم الاشتراك
        await update.message.reply_text(
            "🛑 **عذراً، يجب عليك الاشتراك في القناة أولاً لتتمكن من استخدام البوت!**\n"
            f"اشترك هنا: {CHANNEL_LINK}\n\n"
            "بعد الاشتراك، أرسل الرابط مرة أخرى."
        )
        return

    # 4.2 معالجة الرابط والتحميل
    
    # رسالة جاري المعالجة
    status_message = await update.message.reply_text("⏳ جاري معالجة الرابط وبدء التحميل، يرجى الانتظار...")
    
    # تهيئة yt-dlp
    ydl_opts = {
        'format': 'best',  # اختيار أفضل جودة
        'outtmpl': f'downloads/{user_id}_%(title)s.%(ext)s', # مسار واسم الملف
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 200 * 1024 * 1024, # تحديد أقصى حجم تحميل (200 ميجابايت كحد أقصى معقول للإرسال)
    }
    
    file_path = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # التحقق أولاً من معلومات الفيديو
            info_dict = ydl.extract_info(message_text, download=False)
            
            # إذا كان حجم الملف يتجاوز الحد المسموح به
            if info_dict.get('filesize', 0) > 200 * 1024 * 1024 and info_dict.get('ext') in ['mp4', 'webm']:
                 await status_message.edit_text(
                    f"⚠️ حجم الملف كبير جداً. تجاوز الحد المسموح به (200 ميجابايت). حاول مع رابط آخر."
                )
                 return

            # بدء التحميل الفعلي
            ydl.download([message_text])
            file_path = ydl.prepare_filename(info_dict)

        await status_message.edit_text("✅ تم التحميل بنجاح! جاري الإرسال إلى تيليجرام...")
        
        # 4.3 إرسال الملف
        
        # إرسال كفيديو إذا كان امتداد فيديو معروف
        if info_dict.get('ext') in ['mp4', 'webm', 'mkv', 'avi']:
             await update.message.reply_video(
                video=open(file_path, 'rb'),
                caption=f"تم التحميل بواسطة @dfcbot",
                supports_streaming=True
            )
        else:
            # إرسال كملف عادي (Document)
            await update.message.reply_document(
                document=open(file_path, 'rb'),
                caption=f"تم التحميل بواسطة @dfcbot"
            )

        await status_message.edit_text("🎉 تم إرسال الملف إليك بنجاح!")

    except Exception as e:
        logger.error(f"Download/Upload Error: {e}")
        await status_message.edit_text(
            f"❌ حدث خطأ أثناء التحميل أو المعالجة.\n"
            f"قد يكون الرابط غير مدعوم أو هناك مشكلة في الموقع.\n"
            f"الخطأ: {str(e)[:100]}..."
        )
    finally:
        # 4.4 تنظيف وحذف الملفات المؤقتة
        await status_message.delete()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
