import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from crypto import advanced_algorithm
from predictor import predict_tai_xiu

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN",
    "8862072402:AAG2T5KXVsaqSQPsQ25sj-HkClBExDVz7Jk",
)

user_state: dict[int, dict] = {}

WELCOME = (
    "👋 *Tool MD5 + Hash + Dự đoán Tài/Xỉu*\n\n"
    "🧠 Bot *tự động nhận diện* loại input:\n"
    "• 32 ký tự hex → *MD5*\n"
    "• 64 ký tự hex → *Hash*\n\n"
    "📥 *Cách dùng:*\n"
    "• Gửi 1 trong 2 → bot chờ nhập cái còn lại\n"
    "• Hoặc gửi cả 2 trên 1 dòng: `md5 hash`\n\n"
    "📊 Bot sẽ trả về:\n"
    "• Hash nâng cao (thuật toán custom)\n"
    "• Dự đoán TÀI / XỈU kèm % tin cậy\n\n"
    "Gõ /help để xem thêm."
)


def _is_hex(s: str, length: int) -> bool:
    return len(s) == length and all(c in "0123456789abcdef" for c in s.lower())


def _detect_type(token: str):
    if _is_hex(token, 32):
        return "md5"
    if _is_hex(token, 64):
        return "hash"
    return None


def _format_result(result: dict, prediction: dict) -> str:
    pred = prediction["prediction"]
    conf = prediction["confidence"]
    emoji = "🔴" if pred == "TÀI" else "🔵"
    bar_len = int(conf / 5)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    bd = prediction["breakdown"]

    return (
        "✅ *KẾT QUẢ PHÂN TÍCH*\n\n"
        f"🔸 MD5   : `{result['md5']}`\n"
        f"🔸 Hash  : `{result['hash']}`\n"
        f"🔸 Sig   : `{result['signature']}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔐 *HASH NÂNG CAO (64 hex):*\n"
        f"`{result['result']}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{emoji} *DỰ ĐOÁN: {pred}*\n"
        f"📊 Điểm       : `{prediction['score']}/100`\n"
        f"🎯 Tin cậy    : `{conf}%`\n"
        f"`{bar}`\n\n"
        "🧩 *Chi tiết thuật toán:*\n"
        f"  • Tần suất   : `{bd['freq']}%`\n"
        f"  • Vị trí     : `{bd['pos']}%`\n"
        f"  • Hash chain : `{bd['chain']}%`\n"
        f"  • Entropy    : `{bd['entropy']}%`\n"
        f"  • XOR        : `{bd['xor']}%`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔐 *SHA512 full (128 hex):*\n"
        f"`{result_TYPE['sha512_full']}`"
):
    )


async def cmd_start(   update: Update, ctx: ContextTypes u.DEFAULT_TYPE):
    await update =.message.reply_text(WELCOME update, parse_mode="Markdown")


async def.e cmd_help(update: Update,ff ctx: ContextTypes.DEFAULTective_TYPE):
    await update.message.reply_text(
_user        "📖 *HƯỚNG DẪ
N*\n\n"
        "🧠 *T   ự động nhận diện:*\n"
 await        "• Nhập 32 ký tự update → bot nhận là MD5\n"
        "•.message Nhập 64 ký tự.re → bot nhận là Hash\n"
        "•ply Nhập cả 2 cách nhau_text dấu cách → xử lý ng(fay\n\n"
        "Lệnh khác:\n""
        "• /cancel — huỷ phiên\n🆔"
        "• /id — ` xem user id",
        parse_mode{="Markdown",
    )


async def cmd_idu(update: Update, ctx: ContextTypes.DEFAULT.id}`", parse_mode="Markdown")


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_state.pop(update.effective_user.id, None)
    await update.message.reply_text("❌ Đã huỷ phiên.")


async def _process(update: Update, md5: str, hash64: str):
    try:
        result = advanced_algorithm(md5, hash64)
        prediction = predict_tai_xiu(md5, hash64, result["result"])
        await update.message.reply_text(
            _format_result(result, prediction),
            parse_mode="Markdown",
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")
    except Exception as e:
        log.exception("Process error")
        await update.message.reply_text(f"💥 Lỗi hệ thống: {e}")


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip().lower()
    state = user_state.get(uid, {})
    tokens = text.split()

    # Trường hợp gửi 2 token cùng lúc
    if len(tokens) == 2:
        t1, t2 = tokens
        d1, d2 = _detect_type(t1), _detect_type(t2)
        if d1 == "md5" and d2 == "hash":
            user_state.pop(uid, None)
            await _process(update, t1, t2)
            return
        if d1 == "hash" and d2 == "md5":
            user_state.pop(uid, None)
            await _process(update, t2, t1)
            return
        await update.message.reply_text("⚠️ Cần 1 MD5 (32 hex) và 1 Hash (64 hex).")
        return

    # Trường hợp gửi 1 token (auto-detect)
    if len(tokens) == 1:
        token = tokens[0]
        dtype = _detect_type(token)

        if dtype is None:
            await update.message.reply_text(
                "⚠️ Không nhận diện được!\n"
                "• MD5: 32 ký tự hex\n• Hash: 64 ký tự hex",
            )
            return

        if dtype == "md5":
            state["md5"] = token
            if "hash" in state:
                hash64 = state.pop("hash")
                user_state.pop(uid, None)
                await _process(update, token, hash64)
                return
            user_state[uid] = state
            await update.message.reply_text(
                "🔍 Đã nhận diện: *MD5* (32 ký tự)\n👉 Gửi tiếp *HASH* (64 ký tự).",
                parse_mode="Markdown",
            )
            return

        if dtype == "hash":
            state["hash"] = token
            if "md5" in state:
                md5 = state.pop("md5")
                user_state.pop(uid, None)
                await _process(update, md5, token)
                return
            user_state[uid] = state
            await update.message.reply_text(
                "🔍 Đã nhận diện: *HASH* (64 ký tự)\n👉 Gửi tiếp *MD5* (32 ký tự).",
                parse_mode="Markdown",
            )
            return

    await update.message.reply_text("⚠️ Cú pháp không đúng. Gõ /help để xem hướng dẫn.")


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app


def run_bot():
    log.info("🚀 Bot starting (polling)...")
    app = build_app()
    app.run_polling(drop_pending_updates=True)
