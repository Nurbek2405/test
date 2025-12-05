# bot.py — 100% рабочий финал с зелёными/красными квадратами
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from questions import questions

BOT_TOKEN = "8397130065:AAGDA4or6syVF_q_qrNkxJwgihrIR-f_oYk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_data = {}


def get_keyboard(q_num: int, highlight: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for i, text in enumerate(questions[q_num]["opts"]):
        if not text.strip():
            continue
        prefix = ""
        if highlight is not None:
            if i == questions[q_num]["correct"]:
                prefix = "🟩 "   # настоящий зелёный квадрат
            elif i == highlight:
                prefix = "🟥 "   # настоящий красный квадрат
        buttons.append(InlineKeyboardButton(
            text=prefix + text,
            callback_data=f"ans_{q_num}_{i}" if highlight is None else "ignore"
        ))

    buttons.append(InlineKeyboardButton(text="Завершить тест", callback_data="finish"))
    rows = [buttons[i:i+2] for i in range(0, len(buttons)-1, 2)]
    rows.append([buttons[-1]])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_results(uid: int) -> str:
    d = user_data[uid]
    total = len(questions)
    percent = d["score"] / total * 100

    text = f"<b>Тест завершён!</b>\n\n"
    text += f"Правильных: <b>{d['score']}</b> из <b>{total}</b> ({percent:.1f}%)\n\n"

    # ИСПРАВЛЕНО: теперь переменная errors определена
    errors = [a for a in d["answers"] if a["chosen"] != a["correct"]]

    if errors:
        text += "<b>Ошибки:</b>\n"
        for e in errors:
            qn = e["q"] + 1
            chosen = questions[e["q"]]["opts"][e["chosen"]]
            correct = questions[e["q"]]["opts"][e["correct"]]
            short_q = questions[e["q"]]["q"].split("\n", 1)[1][:80]
            text += f"<b>{qn}.</b> {short_q}…\n"
            text += f"   Вы: 🟥 {chosen}\n"
            text += f"   Правильно: 🟩 <b>{correct}</b>\n\n"
    else:
        text += "Ошибок нет — вы гений!\n"

    text += "\n/start — пройти заново"
    return text


@dp.message(Command("start"))
async def start(message):
    uid = message.from_user.id
    user_data[uid] = {"current": 0, "score": 0, "answers": []}
    await message.answer("АНГ 25.04 — 50 вопросов\n\n" + questions[0]["q"], reply_markup=get_keyboard(0))


@dp.callback_query(lambda c: c.data and (c.data.startswith("ans_") or c.data in ["finish", "ignore"]))
async def process(callback):
    uid = callback.from_user.id
    if uid not in user_data:
        return

    if callback.data == "finish":
        await callback.message.edit_text(get_results(uid), reply_markup=None)
        del user_data[uid]
        return

    if callback.data == "ignore":
        return

    _, q_num_str, choice_str = callback.data.split("_")
    q_num = int(q_num_str)
    choice = int(choice_str)
    correct = questions[q_num]["correct"]

    user_data[uid]["answers"].append({"q": q_num, "chosen": choice, "correct": correct})
    if choice == correct:
        user_data[uid]["score"] += 1

    # Подсветка квадратами
    await callback.message.edit_reply_markup(reply_markup=get_keyboard(q_num, highlight=choice))

    await asyncio.sleep(1.8)

    user_data[uid]["current"] += 1
    next_q = user_data[uid]["current"]

    if next_q >= len(questions):
        await callback.message.edit_text(get_results(uid), reply_markup=None)
        del user_data[uid]
    else:
        await callback.message.edit_text(
            questions[next_q]["q"],
            reply_markup=get_keyboard(next_q)
        )


async def main():
    print("Бот запущен — зелёные и красные квадраты работают идеально!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())