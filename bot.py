import re
import os
import threading
from datetime import datetime
from dotenv import load_dotenv
import telebot
from database import Database
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from calculator import Calculator
from converter import UnitConverter         

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN","BOT TOKEN HERE")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", num_threads=4)
calc = Calculator()
db = Database()
uconv = UnitConverter()

_user_state: dict[int, dict] = {}
_state_lock = threading.Lock()


def get_first_name(message) -> str:
    return message.from_user.first_name or "friend"


def greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 18:
        return "Good afternoon"
    return "Good evening"


def main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("🧮 Calculate"),
        KeyboardButton("🔄 Convert units"),
        KeyboardButton("📜 My history"),
        KeyboardButton("📊 Stats"),
        KeyboardButton("❓ Help"),
    )
    return kb


def fmt_result(expression: str, result) -> str:
    return f"<b>{expression} = {result}</b>  ✅✅"


def set_state(user_id: int, **kwargs):
    with _state_lock:
        _user_state[user_id] = kwargs


def get_state(user_id: int) -> dict:
    with _state_lock:
        return _user_state.get(user_id, {})


def clear_state(user_id: int):
    with _state_lock:
        _user_state.pop(user_id, None)


_BINARY = re.compile(
    r'^\s*(-?\d+(?:\.\d+)?)\s*([+\-*/^])\s*(-?\d+(?:\.\d+)?)\s*$'
)
_UNARY = re.compile(
    r'^\s*(sqrt|log|log10|sin|cos|tan)\s+(-?\d+(?:\.\d+)?)\s*$',
    re.IGNORECASE,
)
_OP_MAP = {'+': '+', '-': '-', '*': '*', '/': '/', '^': 'pow'}
_UNARY_MAP = {'sqrt': 'sqrt', 'log': 'log', 'log10': 'log10', 'sin': 'sin', 'cos': 'cos', 'tan': 'tan'}


def parse_expression(text: str):
    m = _BINARY.match(text)
    if m:
        return _OP_MAP[m.group(2)], float(m.group(1)), float(m.group(3))
    m = _UNARY.match(text)
    if m:
        return _UNARY_MAP[m.group(1).lower()], float(m.group(2)), None
    return None


def do_calculate(message, text: str) -> bool:
    parsed = parse_expression(text)
    if parsed is None:
        return False

    operation, num1, num2 = parsed
    try:
        result = calc.calculate(operation, num1, num2)
        expression = calc.format_expression(operation, num1, num2)
    except ZeroDivisionError:
        bot.reply_to(message, "❌ Division by zero is not allowed.")
        return True
    except ValueError as e:
        bot.reply_to(message, f"❌ {e}")
        return True
    except Exception:
        bot.reply_to(message, "❌ Something went wrong — please try again.")
        return True

    db.save_calculation(expression, result, operation, source='telegram')
    bot.reply_to(message, fmt_result(expression, result))
    return True


@bot.message_handler(commands=['start'])
def cmd_start(message):
    name = get_first_name(message)
    hi = greeting()
    text = (
        f"{hi}, <b>{name}!</b> 👋\n\n"
        f"I'm your <b>Calculator Bot</b> — powered by the same engine as the web app.\n\n"
        "<b>What I can do:</b>\n"
        "  🧮 Calculate — just type any expression\n"
        "  🔄 Convert units (length, weight, temperature)\n"
        "  📜 Show your calculation history\n"
        "  📊 Show stats & breakdowns\n\n"
        "<b>Try it right now:</b> type <code>5 + 3</code> or tap a button below 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "❓ Help")
def cmd_help(message):
    name = get_first_name(message)
    text = (
        f"<b>Hey {name}! Here's everything I can do:</b>\n\n"
        "<b>🧮 Calculations — just type:</b>\n"
        "  <code>5 + 3</code>       addition\n"
        "  <code>10 - 2.5</code>    subtraction\n"
        "  <code>6 * 7</code>       multiplication\n"
        "  <code>8 / 4</code>       division\n"
        "  <code>2 ^ 8</code>       power\n"
        "  <code>sqrt 16</code>     square root\n"
        "  <code>log 100</code>     logarithm\n"
        "  <code>log10 100</code>   log base 10\n"
        "  <code>sin 30</code>      sine\n"
        "  <code>cos 45</code>      cosine\n"
        "  <code>tan 60</code>      tangent\n\n"
        "<b>🔄 Unit converter:</b>\n"
        "  Tap <b>Convert units</b> and follow the steps.\n"
        "  Supports: length · weight · temperature\n\n"
        "<b>📜 History:</b>\n"
        "  Your last 10 calculations with source badge.\n\n"
        "<b>📊 Stats:</b>\n"
        "  Totals, top operations, avg/min/max results.\n\n"
        "No commands needed — just type and go! 🚀"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.message_handler(commands=['history'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "📜 My history")
def cmd_history(message):
    name = get_first_name(message)
    rows = db.get_all()

    if not rows:
        bot.send_message(
            message.chat.id,
            f"No calculations yet, <b>{name}</b>!\n"
            "Send me something like <code>5 + 3</code> to get started.",
            reply_markup=main_keyboard()
        )
        return

    recent = rows[:10]
    lines = [f"<b>📜 Last {len(recent)} calculations, {name}:</b>\n"]
    for r in recent:
        badge = "🔵 Tg" if r.get("source") == "telegram" else "🟢 Web"
        lines.append(f"  {badge}  <code>{r['expression']} = {r['result']}</code>")

    lines.append(f"\n<i>Total in database: {len(rows)}</i>")
    bot.send_message(message.chat.id, "\n".join(lines), reply_markup=main_keyboard())


@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "📊 Stats")
def cmd_stats(message):
    name = get_first_name(message)
    stats = db.get_stats()

    if not stats["total"]:
        bot.send_message(
            message.chat.id,
            f"No data yet, <b>{name}</b>! Make some calculations first.",
            reply_markup=main_keyboard()
        )
        return

    src_lines = []
    for s in stats.get("by_source", []):
        icon = "🔵" if s["source"] == "telegram" else "🟢"
        src_lines.append(f"    {icon} {s['source'].capitalize()}: <b>{s['count']}</b>")

    op_lines = []
    for o in stats.get("by_op", [])[:5]:
        op_lines.append(f"    • {o['operation']}: <b>{o['count']}</b>")

    avg = f"{stats['avg']:.4g}" if stats.get("avg") is not None else "—"
    mn = f"{stats['min']:g}" if stats.get("min") is not None else "—"
    mx = f"{stats['max']:g}" if stats.get("max") is not None else "—"

    text = (
        f"<b>📊 Stats for {name}:</b>\n\n"
        f"Total calculations: <b>{stats['total']}</b>\n\n"
        "<b>By source:</b>\n" + "\n".join(src_lines) + "\n\n"
        "<b>Top operations:</b>\n" + "\n".join(op_lines) + "\n\n"
        "<b>Result values:</b>\n"
        f"    avg <b>{avg}</b>   min <b>{mn}</b>   max <b>{mx}</b>"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


CATEGORIES = ['length', 'weight', 'temperature']


def category_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(c.capitalize(), callback_data=f"cat:{c}") for c in CATEGORIES])
    return kb


def units_keyboard(category: str, step: str) -> InlineKeyboardMarkup:
    try:
        units = uconv.get_units(category)
    except Exception:
        units = []
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(u, callback_data=f"{step}:{u}") for u in units])
    return kb


@bot.message_handler(commands=['convert'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🔄 Convert units")
def cmd_convert(message):
    name = get_first_name(message)
    set_state(message.from_user.id, step="pick_category")
    bot.send_message(
        message.chat.id,
        f"Sure, <b>{name}</b>! First pick a category 👇",
        reply_markup=category_keyboard()
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def cb_category(call):
    category = call.data.split(":", 1)[1]
    uid = call.from_user.id
    set_state(uid, step="pick_from", category=category)
    bot.edit_message_text(
        f"Category: <b>{category}</b>\n\nNow pick the <b>from</b> unit 👇",
        call.message.chat.id, call.message.message_id,
        reply_markup=units_keyboard(category, "from"),
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("from:"))
def cb_from_unit(call):
    from_unit = call.data.split(":", 1)[1]
    uid = call.from_user.id
    state = get_state(uid)
    category = state.get("category", "length")
    set_state(uid, step="pick_to", category=category, from_unit=from_unit)
    bot.edit_message_text(
        f"Category: <b>{category}</b>   From: <b>{from_unit}</b>\n\nNow pick the <b>to</b> unit 👇",
        call.message.chat.id, call.message.message_id,
        reply_markup=units_keyboard(category, "to"),
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("to:"))
def cb_to_unit(call):
    to_unit = call.data.split(":", 1)[1]
    uid = call.from_user.id
    state = get_state(uid)
    category = state.get("category", "length")
    from_u = state.get("from_unit", "")
    set_state(uid, step="enter_value", category=category, from_unit=from_u, to_unit=to_unit)
    bot.edit_message_text(
        f"Category: <b>{category}</b>   <b>{from_u}</b> → <b>{to_unit}</b>\n\n"
        f"Now type the value to convert 👇",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text and m.text.strip() == "🧮 Calculate")
def cmd_calc_button(message):
    name = get_first_name(message)
    set_state(message.from_user.id, step="calculating")
    bot.send_message(
        message.chat.id,
        f"Go ahead, <b>{name}</b>! Type your expression:\n\n"
        "<code>5 + 3</code>  ·  <code>sqrt 16</code>  ·  <code>2 ^ 8</code>",
        reply_markup=main_keyboard()
    )


@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    text = message.text.strip()
    state = get_state(uid)
    name = get_first_name(message)

    if state.get("step") == "enter_value":
        try:
            val = float(text.replace(",", "."))
            category = state["category"]
            from_u = state["from_unit"]
            to_u = state["to_unit"]
            result = uconv.convert(category, val, from_u, to_u)
            clear_state(uid)
            bot.reply_to(
                message,
                f"<b>{val} {from_u} = {result:.6g} {to_u}</b>\n\n"
                "Want another? Tap <b>Convert units</b> again.",
                reply_markup=main_keyboard()
            )
        except ValueError:
            bot.reply_to(message, "❌ Please send a valid number, e.g. <code>100</code>")
        except Exception as e:
            clear_state(uid)
            bot.reply_to(message, f"❌ Conversion error: {e}", reply_markup=main_keyboard())
        return

    if do_calculate(message, text):
        clear_state(uid)
        return

    bot.reply_to(
        message,
        f"Hmm, I didn't get that, <b>{name}</b>. 🤔\n\n"
        "Type a calculation like <code>5 + 3</code>, or tap a button below.",
        reply_markup=main_keyboard()
    )


if __name__ == '__main__':
    print("🤖  Bot is running — polling...  (Ctrl+C to stop)")
    bot.infinity_polling(timeout=20, long_polling_timeout=15)