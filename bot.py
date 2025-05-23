# -*- coding: utf-8 -*-
import logging
import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
from telegram.constants import ChatMemberStatus
from tiktok_downloader import snaptik

# إعدادات البوت
TOKEN = "848477745:AAE2jCkC_Ll5peJ_oOhdk-uh_6eWV3l7_iY"  # استبدل هذا بالتوكن الخاص ببوتك
CHANNEL_ID = "@Typo2020"  # معرف القناة المطلوب الانضمام إليها

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# النصوص المترجمة
translations = {
    'ar': {
        'welcome': "أهلاً بك! أرسل لي رابط فيديو تيك توك لتحميله بدون علامة مائية.",
        'join_channel': f"عذراً، يجب عليك الانضمام إلى القناة {CHANNEL_ID} أولاً لاستخدام البوت.",
        'membership_error': "حدث خطأ أثناء التحقق من عضويتك في القناة. يرجى المحاولة مرة أخرى لاحقاً.",
        'invalid_link': "الرجاء إرسال رابط فيديو تيك توك صالح.",
        'downloading': "جاري تحميل الفيديو، يرجى الانتظار...",
        'download_success': "تم التحميل بنجاح!",
        'no_video_found': "لم يتم العثور على فيديوهات قابلة للتحميل.",
        'processing_error': "حدث خطأ أثناء معالجة الفيديو.",
        'download_failed': "عذراً، لم أتمكن من تحميل الفيديو. قد يكون الرابط غير صحيح أو أن الخدمة تواجه مشكلة.",
        'general_error': "عذراً، حدث خطأ أثناء محاولة تحميل الفيديو. يرجى المحاولة مرة أخرى لاحقاً."
    },
    'en': {
        'welcome': "Welcome! Send me a TikTok video link to download it without a watermark.",
        'join_channel': f"Sorry, you must join the channel {CHANNEL_ID} first to use the bot.",
        'membership_error': "An error occurred while checking your channel membership. Please try again later.",
        'invalid_link': "Please send a valid TikTok video link.",
        'downloading': "Downloading the video, please wait...",
        'download_success': "Downloaded successfully!",
        'no_video_found': "No downloadable videos found.",
        'processing_error': "An error occurred while processing the video.",
        'download_failed': "Sorry, I couldn't download the video. The link might be incorrect or the service is having issues.",
        'general_error': "Sorry, an error occurred while trying to download the video. Please try again later."
    }
}

# دالة للحصول على النص المترجم بناءً على لغة المستخدم
def get_text(language_code: str, key: str) -> str:
    # الافتراضي إلى العربية إذا لم تكن اللغة 'en'
    lang = 'en' if language_code == 'en' else 'ar'
    return translations[lang].get(key, translations['ar'].get(key, "Error: Text not found")) # Fallback to Arabic then error message

# دالة للتحقق من عضوية المستخدم في القناة
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    lang_code = update.effective_user.language_code
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        else:
            await update.message.reply_text(get_text(lang_code, 'join_channel'))
            return False
    except Exception as e:
        logger.error(f"حدث خطأ أثناء التحقق من العضوية للمستخدم {user_id}: {e}")
        await update.message.reply_text(get_text(lang_code, 'membership_error'))
        return False

# دالة لمعالجة أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang_code = update.effective_user.language_code
    await update.message.reply_text(get_text(lang_code, 'welcome'))

# دالة لمعالجة روابط تيك توك
async def handle_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang_code = update.effective_user.language_code
    if not await check_membership(update, context):
        return

    url = update.message.text
    if "tiktok.com" not in url:
        await update.message.reply_text(get_text(lang_code, 'invalid_link'))
        return

    await update.message.reply_text(get_text(lang_code, 'downloading'))

    try:
        # استخدام مكتبة tiktok_downloader (خدمة snaptik كمثال)
        videos = snaptik(url)
        if videos:
            logger.info(f"Videos object for user {update.effective_user.id}: {videos}")
            try:
                # تحميل الفيديو الأول (عادة بدون علامة مائية) إلى ملف مؤقت
                video_path = f"/home/ubuntu/tiktok_downloader_bot/temp_video_{update.effective_user.id}.mp4"
                videos[0].download(video_path)
                # إرسال الفيديو المحمل
                await update.message.reply_video(video=open(video_path, 'rb'), caption=get_text(lang_code, 'download_success'))
                # حذف الملف المؤقت
                try:
                    os.remove(video_path)
                except OSError as remove_err:
                    logger.error(f"Error removing temp file {video_path}: {remove_err}")
            except IndexError:
                 await update.message.reply_text(get_text(lang_code, 'no_video_found'))
            except Exception as download_err:
                 logger.error(f"خطأ أثناء تحميل أو إرسال الفيديو للمستخدم {update.effective_user.id}: {download_err}")
                 await update.message.reply_text(get_text(lang_code, 'processing_error'))
        else:
            await update.message.reply_text(get_text(lang_code, 'download_failed'))
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تحميل الفيديو للمستخدم {update.effective_user.id}: {e}")
        await update.message.reply_text(get_text(lang_code, 'general_error'))

# دالة لمعالجة تحديثات عضوية الدردشة (اختياري، للترحيب مثلاً)
async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # يمكنك إضافة منطق هنا للتعامل مع انضمام أو مغادرة المستخدمين للبوت أو القناة إذا لزم الأمر
    pass

def main() -> None:
    """بدء تشغيل البوت."""
    # إنشاء التطبيق وتمرير توكن البوت
    application = Application.builder().token(TOKEN).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_link))
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

    # تشغيل البوت حتى يتم الضغط على Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

