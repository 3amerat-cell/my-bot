import os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.environ.get("TOKEN")

# --- قائمة الحظر الاباحي ---
BAD_WORDS = ["porn","pornhub","xvideos","xnxx","xhamster","redtube","brazzers","onlyfans","youporn","sex","xxx","adult","erotic","nude","nsfw","سكس","اباحي","جنس","مثير","عاري"]
BAD_SITES = ["pornhub.com","xvideos.com","xnxx.com","xhamster.com","redtube.com","brazzers.com","onlyfans.com","youporn.com","porn.com"]

def is_porn(url, info=None):
    info = info or {}
    text = (url + " " + str(info.get("title","")) + " " + str(info.get("description","")) + " " + str(info.get("uploader","")) + " " + str(info.get("channel","")) + " " + str(info.get("categories",""))).lower()
    # 1. لو الموقع نفسه اباحي
    for s in BAD_SITES:
        if s in url.lower():
            return True
    # 2. لو العنوان او الوصف فيه كلمة اباحية
    for w in BAD_WORDS:
        if w in text:
            return True
    # 3. لو الفيديو محدد +18
    if info.get("age_limit", 0) and info.get("age_limit") >= 18:
        return True
    return False

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بيك في بوت التحميل 🔥\n\n✅ اختار الجودة البتناسبك\n⛔ اي فيديو اباحي بيترفض تلقائياً\n\nرسل رابط هسي 👇")

async def ask_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("رسل رابط صحيح 👌")
        return
    # فحص قبل اي شي
    if is_porn(url):
        await update.message.reply_text("⛔ عذراً\nالفيديو دا اباحي وممنوع 🚫\nالبوت دا للفيديوهات النظيفة بس.")
        return
    context.user_data["url"] = url
    keyboard = [
        [InlineKeyboardButton("🎬 1080p عالية", callback_data="1080"),
         InlineKeyboardButton("🎬 720p متوسطة", callback_data="720")],
        [InlineKeyboardButton("🎬 480p خفيفة", callback_data="480"),
         InlineKeyboardButton("🎬 360p ضعيفة", callback_data="360")],
        [InlineKeyboardButton("🎵 صوت بس MP3", callback_data="audio")],
    ]
    await update.message.reply_text("اختار الجودة 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def do_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    url = context.user_data.get("url")
    choice = q.data
    await q.edit_message_text(f"⏳ جاري التحميل بجودة {choice} ...")
    try:
        if choice == "audio":
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'audio.%(ext)s', 'quiet': True, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]}
        else:
            ydl_opts = {'format': f'bestvideo[height<={choice}]+bestaudio/best[height<={choice}]/best', 'outtmpl': 'video.%(ext)s', 'quiet': True, 'merge_output_format': 'mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # فحص تاني بعد ما عرفنا عنوان الفيديو الحقيقي
            if is_porn(url, info):
                await q.edit_message_text("⛔ تم رفض الفيديو\nالمحتوى دا اباحي وممنوع 🚫")
                return
            fname = ydl.prepare_filename(info)
            if choice == "audio":
                fname = "audio.mp3"
        if choice == "audio":
            with open(fname, 'rb') as f:
                await q.message.reply_audio(audio=f, caption="تم ✅ صوت")
        else:
            with open(fname, 'rb') as f:
                await q.message.reply_video(video=f, caption=f"تم ✅ جودة {choice}p")
        os.remove(fname)
        await q.edit_message_text("تم ✅ رسل رابط تاني")
    except Exception as e:
        await q.edit_message_text(f"حصل خطأ 😥 جرب جودة 360\n{e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_quality))
    app.add_handler(CallbackQueryHandler(do_download))
    print("Bot is running...")
    app.run_polling()