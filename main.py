import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ChatMemberStatus
from yt_dlp import YoutubeDL
import os

# ----------------------------------------------------------------------
# 1. إعدادات البوت والتوكن والقناة
# التوكن: 431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk
BOT_TOKEN = "431609800:AAHhRRmrC5wYk3V1uK5a-aRZO7aBDZvvTIk"
# ID القناة الرقمي (المطلوب): -1002014674719
REQUIRED_CHANNEL_ID = -1002014674719
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
        # المستخدم مشترك إذا كان 'member' ليس BANNED أو LEFT
        is_subscribed = member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED)
        return is_subscribed
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        # إذا فشل التحقق (لأن البوت ليس مسؤولاً)، نعتبره غير مشترك لتجنب إساءة الاستخدام
        return False

# ----------------------------------------------------------------------
# 3. دالة معالج أمر /start
async def start_command(update: Update, context) -> None:
    """يرد على أمر /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً بك يا {user.mention_html()}!\n\n"
        "أنا بوت التحميل. أرسل لي رابط أي فيديو/ملف وسأحاول تحميله لك من معظم المواقع."
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
        'format': 'best',  # اختيار أفضل جودة تلقائياً
        'outtmpl': f'downloads/{user_id}_%(title)s.%(ext)s', # مسار واسم الملف
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 200 * 1024 * 1024, # تحديد أقصى حجم تحميل (مثال: 200 ميجابايت)
    }
    
    file_path = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # التحقق أولاً من معلومات الفيديو دون تحميل (لتقليل الخطأ)
            info_dict = ydl.extract_info(message_text, download=False)
            
            # إذا كان حجم الملف يتجاوز الحد المسموح به في تيليجرام، نرسل تنبيهاً
            if info_dict.get('filesize', 0) > 200 * 1024 * 1024 and info_dict.get('ext') in ['mp4', 'webm']:
                 await status_message.edit_text(
                    f"⚠️ حجم الملف كبير جداً ({info_dict.get('filesize_approx', 'غير معروف')}). البوت محدود بحجم 200 ميجابايت."
                )
                 return

            # بدء التحميل الفعلي
            ydl.download([message_text])
            file_path = ydl.prepare_filename(info_dict)

        await status_message.edit_text("✅ تم التحميل بنجاح! جاري الإرسال إلى تيليجرام...")
        
        # 4.3 إرسال الملف
        
        # تحديد الإرسال كـ فيديو إذا كان الامتداد mp4/webm وحجمه مناسب
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
            f"الخطأ: {str(e)[:100]}..." # عرض جزء من الخطأ
        )
    finally:
        # 4.4 تنظيف وحذف الملفات المؤقتة
        await status_message.delete()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")

# ----------------------------------------------------------------------
# 5. الدالة الرئيسية لتشغيل البوت
def main() -> None:
    """يشغل البوت."""
    
    # تأكد من وجود مجلد التحميلات
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة المعالجات (Handlers)
    application.add_handler(CommandHandler("start", start_command))
    # يستقبل كل رسالة نصية قد تكون رابطاً (باستثناء الأوامر)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # بدء تشغيل البوت (Polling)
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
