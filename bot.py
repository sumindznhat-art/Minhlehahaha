import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from crypto import advanced_algorithm

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("8862072402:AAG2T5KXVsaqSQPsQ25sj-HkClBExDVz7Jk")
if not BOT_TOKEN:
    raise RuntimeError("Thiếu biến môi trường BOT_TOKEN!")

user_state: dict[int, dict] = {}

WELCOME = (
    "👋 *Tool MD5 + Hash Custom Algorithm*\n\n"
    "Gửi cho tôi theo cú pháp:\n"
    "`<MD5_32> <HASH_64>`\n\n"
    "Ví dụ:\n"
    "`d41d8cd98f00b204e9800998ecf8427e "
    "e3b0c44298fc1c149afbf4c8996fb924"
    "27ae41e4649b934ca495991b7852b855`\n\n"
    "Hoặc dùng /step để nhập từng bước."
)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME, parse_mode="Markdown")

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Hướng dẫn*\n"
        "• Gửi `md5 hash` trên 1 dòng\n"
        "• /step — nhập tuần tự MD5 → Hash\n"
        "• /cancel — huỷ phiên\n"
        "• /id — xem user id",
        parse_mode="Markdown",
    )

async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f"🆔 `{u.id}`", parse_mode="Markdown")

async def cmd_step(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = {"step": "md5"}
    await update.message.reply_text("🔹 Bước 1/2: Gửi **MD5** (32 ký tự hex).", parse_mode="Markdown")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_state.pop(update.effective_user.id, None)
    await update.message.reply_text("❌ Đã huỷ phiên.")

def _format_result(r: dict) -> str:
    return (
        "✅ *KẾT QUẢ*\n\n"
        f"🔸 MD5   : `{r['md5']}`\n"
        f"🔸 Hash  : `{r['hash']}`\n"
        f"🔸 Sig   : `{r['signature']}`\n\n"
        "🎯 *RESULT (64 hex):*\n"
        f"`{r['result']}`\n\n"
        "🔐 *SHA512 full (128 hex):*\n"
        f"`{r['sha512_full']}`"
    )

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    state = user_state.get(uid)

    try:
        if state:
            if state["step"] == "md5":
                if len(text) != 32:
                    raise ValueError("MD5 phải đúng 32 ký tự.")
                state["md5"] = text
                state["step"] = "hash"
                await update.message.reply_text("🔹 Bước 2/2: Gửi **Hash** (64 ký tự hex).", parse_mode="Markdown")
                return
            if state["step"] == "hash":
                md5 = state["md5"]
                user_state.pop(uid, None)
                result = advanced_algorithm(md5, text)
                await update.message.reply_text(_format_result(result), parse_mode="Markdown")
                return

        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text(
                "⚠️ Cần đúng 2 giá trị: `<MD5_32> <HASH_64>`.\nGõ /help để xem hướng dẫn.",
                parse_mode="Markdown",
            )
            return

        result = advanced_algorithm(parts[0], parts[1])
        await update.message.reply_text(_format_result(result), parse_mode="Markdown")

    except ValueError as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")
    except Exception as e:
        log.exception("Unexpected error")
        await update.message.reply_text(f"💥 Lỗi hệ thống: {e}")

def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("step", cmd_step))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app

def run_bot():
    log.info("🚀 Bot starting (polling)...")
    app = build_app()
    app.run_polling(drop_pending_updates=True)
