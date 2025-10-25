"""
بوت موجز - النسخة الكاملة
ملخص ذكي لفيديوهات اليوتيوب مع Google Gemini AI
"""

import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import google.generativeai as genai

# ===============================
# إعدادات البوت والقناة
# ===============================
BOT_TOKEN = "8458698977:AAGvA4FnEPcYbHA8iD00z1gHZACMBBA8IWQ"
CHANNEL_ID = "@android_4"
CHANNEL_URL = "https://t.me/android_4"

# مفتاح Google Gemini API
GOOGLE_AI_API_KEY = "AIzaSyC38L4glnxyoIlebb3nuLV5wzpHXjiTekE"

# تهيئة Gemini API
genai.configure(api_key=GOOGLE_AI_API_KEY)

# إعداد نظام السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===============================
# دالة التحقق من الاشتراك في القناة
# ===============================
async def check_user_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
    """
    التحقق من اشتراك المستخدم في القناة
    
    Returns:
        tuple: (is_subscribed: bool, error_message: str)
    """
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        logger.info(f"حالة المستخدم {user_id} في القناة: {member.status}")
        
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True, ""
        elif member.status == ChatMemberStatus.LEFT:
            return False, "غادرت القناة"
        elif member.status == ChatMemberStatus.KICKED:
            return False, "محظور"
        else:
            return False, f"حالة غير معروفة: {member.status}"
            
    except TelegramError as e:
        error_msg = str(e)
        logger.error(f"خطأ في التحقق من الاشتراك: {error_msg}")
        
        if "bot was blocked" in error_msg.lower():
            return False, "❌ خطأ: المستخدم حظر البوت"
        elif "chat not found" in error_msg.lower():
            return False, "❌ خطأ: القناة غير موجودة"
        elif "bot is not a member" in error_msg.lower() or "participant" in error_msg.lower():
            return False, "⚠️ البوت ليس مسؤولاً في القناة!"
        else:
            return False, f"❌ خطأ تقني: {error_msg[:100]}"
    
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return False, f"❌ خطأ: {str(e)[:100]}"

# ===============================
# رسالة طلب الاشتراك مع الأزرار
# ===============================
async def send_subscription_message(update: Update, error_msg: str = ""):
    keyboard = [
        [InlineKeyboardButton("الاشتراك في القناة 📢", url=CHANNEL_URL)],
        [InlineKeyboardButton("تحققت ✅", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "عذراً 🚫\n\n"
        "لاستخدام البوت، يجب عليك أولاً الاشتراك في قناتنا.\n"
        "اشترك الآن ثم اضغط على زر 'تحققت' بالأسفل."
    )
    
    if error_msg and "البوت ليس مسؤولاً" in error_msg:
        message += f"\n\n{error_msg}"
    
    await update.message.reply_text(message, reply_markup=reply_markup)

# ===============================
# معالج زر التحقق من الاشتراك
# ===============================
async def handle_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جارٍ التحقق... ⏳")
    
    user_id = query.from_user.id
    is_subscribed, error_msg = await check_user_subscription(user_id, context)
    
    if is_subscribed:
        welcome_message = (
            "✅ رائع! تم التحقق بنجاح! 🎉\n\n"
            "مرحباً بك في بوت موجز!\n\n"
            "أنا هنا لمساعدتك في تلخيص فيديوهات اليوتيوب بذكاء.\n\n"
            "📌 كيفية الاستخدام:\n"
            "• أرسل لي رابط فيديو يوتيوب\n"
            "• سأقوم بتحليله وتقديم ملخص شامل\n\n"
            "جرّب الآن! 🚀"
        )
        await query.edit_message_text(welcome_message)
    else:
        if "البوت ليس مسؤولاً" in error_msg:
            not_subscribed_message = (
                "⚠️ تنبيه مهم!\n\n"
                f"{error_msg}\n\n"
                "📋 يرجى إضافة @MawjazBot كمسؤول في @android_4\n"
                "مع صلاحية 'See Members' فقط"
            )
        elif error_msg:
            not_subscribed_message = f"❌ {error_msg}\n\nحاول مرة أخرى."
        else:
            not_subscribed_message = (
                "❌ لم تشترك بعد في القناة!\n\n"
                "الرجاء:\n"
                "1️⃣ الاشتراك في @android_4\n"
                "2️⃣ انتظر 5 ثوانٍ\n"
                "3️⃣ اضغط 'تحققت ✅' مرة أخرى"
            )
        
        await query.edit_message_text(not_subscribed_message)
        
        keyboard = [
            [InlineKeyboardButton("الاشتراك في القناة 📢", url=CHANNEL_URL)],
            [InlineKeyboardButton("تحققت ✅", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اشترك وعُد للتحقق:", reply_markup=reply_markup)

# ===============================
# معالج أمر /start
# ===============================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"المستخدم {user_name} (ID: {user_id}) أرسل /start")
    
    is_subscribed, error_msg = await check_user_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_message(update, error_msg)
    else:
        welcome_message = (
            f"مرحباً {user_name}! 👋\n\n"
            "أنا بوت موجز - ملخص ذكي لفيديوهات اليوتيوب 🎬\n\n"
            "📌 كيفية الاستخدام:\n"
            "• أرسل لي رابط أي فيديو يوتيوب\n"
            "• سأقوم بتحليل محتواه وتقديم:\n"
            "  ✓ ملخص شامل في نقاط واضحة\n"
            "  ✓ أهم 3 استنتاجات رئيسية\n"
            "  ✓ صياغة احترافية ومنظمة\n\n"
            "جرّب الآن وأرسل رابط فيديو! 🚀"
        )
        await update.message.reply_text(welcome_message)

# ===============================
# أمر /status
# ===============================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = await context.bot.get_chat(CHANNEL_ID)
        bot_member = await context.bot.get_chat_member(CHANNEL_ID, context.bot.id)
        
        status_msg = (
            "📊 حالة البوت:\n\n"
            f"✅ البوت متصل\n"
            f"✅ القناة: {chat.title}\n"
            f"✅ حالة البوت: {bot_member.status}\n\n"
        )
        
        if bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            status_msg += "✅ البوت مسؤول - يمكنه التحقق من الأعضاء!"
        else:
            status_msg += "⚠️ البوت ليس مسؤولاً!\n\nأضفه كمسؤول مع صلاحية 'See Members'"
        
    except Exception as e:
        status_msg = f"❌ خطأ:\n{str(e)}"
    
    await update.message.reply_text(status_msg)

# ===============================
# أمر /check
# ===============================
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_subscribed, error_msg = await check_user_subscription(user_id, context)
    
    if is_subscribed:
        await update.message.reply_text("✅ أنت مشترك في القناة!\nيمكنك استخدام البوت.")
    else:
        await update.message.reply_text(
            f"❌ غير مشترك\n\n"
            f"السبب: {error_msg if error_msg else 'لم تشترك'}\n\n"
            "اشترك في @android_4"
        )

# ===============================
# استخراج معرّف الفيديو من رابط اليوتيوب
# ===============================
def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

# ===============================
# الحصول على نص الفيديو
# ===============================
def get_video_transcript(video_id: str) -> str:
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['ar'])
        except:
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                transcript = transcript_list.find_transcript(
                    [t.language_code for t in transcript_list]
                )
        
        transcript_data = transcript.fetch()
        full_text = " ".join([entry['text'] for entry in transcript_data])
        
        return full_text
    
    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception as e:
        logger.error(f"خطأ في استخراج النص: {e}")
        return None

# ===============================
# تلخيص النص باستخدام Gemini
# ===============================
async def summarize_with_gemini(transcript: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""أنت خبير في تحليل وتلخيص محتوى الفيديو. هذا نص تم استخراجه من فيديو على يوتيوب. مهمتك هي:

1. تلخيص المحتوى باللغة العربية في 5-7 نقاط رئيسية وموجزة.
2. استخراج أهم 3 استنتاجات أو أفكار (Key Insights) من الفيديو.
3. صياغة الملخص النهائي بطريقة منظمة وواضحة باستخدام العناوين والنقاط.

ابدأ الملخص بعنوان جذاب يعكس محتوى الفيديو.

النص المستخرج:
{transcript[:8000]}

قدم الملخص بصيغة واضحة ومنظمة."""

        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        logger.error(f"خطأ في التلخيص: {e}")
        return None

# ===============================
# معالج الرسائل (روابط اليوتيوب)
# ===============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # التحقق من الاشتراك
    is_subscribed, error_msg = await check_user_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_message(update, error_msg)
        return
    
    # التحقق من صحة رابط اليوتيوب
    video_id = extract_video_id(message_text)
    
    if not video_id:
        await update.message.reply_text(
            "❌ يرجى إرسال رابط يوتيوب صالح.\n\n"
            "مثال:\n"
            "https://www.youtube.com/watch?v=xxxxx\n"
            "أو\n"
            "https://youtu.be/xxxxx"
        )
        return
    
    # إرسال رسالة معالجة
    processing_message = await update.message.reply_text(
        "⏳ جارٍ استخراج النص وتلخيصه...\n"
        "قد يستغرق هذا بعض الوقت، يرجى الانتظار..."
    )
    
    try:
        # الحصول على نص الفيديو
        logger.info(f"استخراج نص الفيديو: {video_id}")
        transcript = get_video_transcript(video_id)
        
        if not transcript:
            await processing_message.edit_text(
                "❌ عذراً، هذا الفيديو لا يحتوي على نص مكتوب، لا يمكنني تلخيصه.\n\n"
                "تأكد من أن الفيديو يحتوي على ترجمة أو نص تلقائي."
            )
            return
        
        logger.info(f"تم استخراج {len(transcript)} حرف من النص")
        
        # تحديث رسالة المعالجة
        await processing_message.edit_text(
            "⏳ تم استخراج النص بنجاح!\n"
            "جارٍ تحليل المحتوى وإنشاء الملخص... 🤖"
        )
        
        # تلخيص النص باستخدام Gemini
        logger.info("إرسال النص إلى Gemini للتلخيص...")
        summary = await summarize_with_gemini(transcript)
        
        if not summary:
            await processing_message.edit_text(
                "❌ عذراً، حدث خطأ أثناء إنشاء الملخص.\n"
                "يرجى المحاولة مرة أخرى لاحقاً."
            )
            return
        
        logger.info("تم إنشاء الملخص بنجاح!")
        
        # إضافة التوقيع
        final_summary = f"{summary}\n\n━━━━━━━━━━━━━━━\nتم التلخيص بواسطة @MawjazBot ✨"
        
        # حذف رسالة المعالجة
        await processing_message.delete()
        
        # إرسال الملخص النهائي
        await update.message.reply_text(final_summary)
        
        logger.info(f"تم إرسال الملخص للمستخدم {user_id}")
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الفيديو: {e}")
        await processing_message.edit_text(
            "❌ عذراً، حدث خطأ غير متوقع.\n"
            "يرجى المحاولة مرة أخرى."
        )

# ===============================
# معالج الأخطاء
# ===============================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ عذراً، حدث خطأ في معالجة طلبك.\n"
            "يرجى المحاولة مرة أخرى."
        )

# ===============================
# الدالة الرئيسية
# ===============================
def main():
    logger.info("🚀 بدء تشغيل بوت موجز (النسخة الكاملة)...")
    logger.info(f"✅ Gemini API Key: {GOOGLE_AI_API_KEY[:20]}...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("check", check_command))
    
    # إضافة معالج أزرار الكالباك
    application.add_handler(CallbackQueryHandler(handle_subscription_check))
    
    # إضافة معالج الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # تشغيل البوت
    logger.info("✅ البوت يعمل الآن! اضغط Ctrl+C للإيقاف.")
    logger.info("📱 جرب البوت على: @MawjazBot")
    
    # وضع Polling للتشغيل المحلي
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
