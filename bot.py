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


def _detect_type(token: str) -> str | None:
    """Nhận diện loại input: 'md5', 'hash' hoặc None."""
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
        f"`{result['sha512_full']}`"
    )


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *HƯỚNG DẪN*\n\n"
        "🧠 *Tự động nhận diện:*\n"
        "• Nhập 32 ký tự → bot nhận là MD5\n"
        "• Nhập 64 ký tự → bot nhận là Hash\n"
        "• Nhập cả 2 cách nhau dấu cách → xử lý ngay\n\n"
        "🎯 *Dự đoán Tài/Xỉu:*\n"
        "Dùng thuật toán 6 tầng:\n"
        "1. Tần suất hex\n"
        "2. Trọng số vị trí\n"
        "3. Hash chain\n"
        "4. Entropy\n"
        "5. Rolling XOR\n"
        "6. Tổng hợp có trọng số\n\n"
        "⚠️ *Lưu ý:* Đây là phân tích toán học, "
        "KHÔNG đảm bảo thắng 100%. Chơi có trách nhiệm.\n\n"
        "Lệnh khác:\n"
        "• /cancel — huỷ phiên\n"
        "• /id — xem user id",
        parse_mode="Markdown",
    )


async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f"🆔 `{u.id}`", parse_mode="Markdown")


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_state.pop(update.effective_user.id, None)
    await update.message.reply_text("❌ Đã huỷ phiên.")


async def _process(update: Update, md5: str, hash64: str):
    """Xử lý khi đã có đủ MD5 + Hash."""
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

    # ═══════ Tách các token ra ═══════
    tokens = text.split()

    # ═══════ Trường hợp 2 token trên 1 dòng ═══════
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

        await update.message.reply_text(
            "⚠️ Không nhận diện được. Cần 1 MD5 (32 hex) và 1 Hash (64 hex).",
        )
        return

    # ═══════ Trường hợp 1 token — auto-detect ═══════
    if len(tokens) == 1:
        token = tokens[0]
        dtype = _detect_type(token)

        if dtype is None:
            await update.message.reply_text(
                "⚠️ Không nhận diện được!\n\n"
                "• MD5 phải là *32 ký tự hex*\n"
                "• Hash phải là *64 ký tự hex*\n\n"
                "Gõ /help để xem hướng dẫn.",
                parse_mode="Markdown",
            )
            return

        # Đã có state trước đó?
        if dtype == "md5":
            state["md5"] = token
            if "hash" in state:
                # Đủ cả 2 → xử lý
                hash64 = state.pop("hash")
                user_state.pop(uid, None)
                await _process(update, token, hash64)
                return
            # Chỉ mới có MD5 → chờ Hash
            user_state[uid] = state
            await update.message.reply_text(
                "🔍 Đã nhận diện: *MD5* (32 ký tự)\n"
                "👉 Giờ gửi tiếp *HASH* (64 ký tự).",
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
                "🔍 Đã nhận diện: *HASH* (64 ký tự)\n"
                "👉 Giờ gửi tiếp *MD5* (32 ký tự).",
                parse_mode="Markdown",
            )
            return

    # ═══════ Nhiều hơn 2 token ═══════
    await update.message.reply_text(
        "⚠️ Cú pháp không đúng. Gõ /help để xem hướng dẫn.",
    )


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
