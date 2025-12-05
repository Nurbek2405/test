# bot.py — финальная версия с выбором тестов, правильными ответами и цветной подсветкой
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from questions import questions  # Первый тест
from questions2 import questions2  # Второй тест

BOT_TOKEN = "8397130065:AAGDA4or6syVF_q_qrNkxJwgihrIR-f_oYk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Список тестов (добавьте новые здесь, импортируя их файлы)
tests = [
    {"name": "АНГ 25.04 (копия)", "questions": questions},
    {"name": "Сливтер жинағы 24.03.2025", "questions": questions2},
]

user_data = {}

def get_test_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i, test in enumerate(tests):
        buttons.append(InlineKeyboardButton(text=test["name"], callback_data=f"start_test_{i}"))
    rows = [buttons[i:i+1] for i in range(0, len(buttons), 1)]  # По 1 тесту в ряд
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_keyboard(test_index: int, q_num: int, highlight: int = None) -> InlineKeyboardMarkup:
    q_list = tests[test_index]["questions"]
    buttons = []
    for i, text in enumerate(q_list[q_num]["opts"]):
        if not text.strip():
            continue
        prefix = ""
        if highlight is not None:
            if i == q_list[q_num]["correct"]:
                prefix = "🟩 "  # зелёный квадрат
            elif i == highlight:
                prefix = "🟥 "  # красный квадрат
        buttons.append(InlineKeyboardButton(
            text=prefix + text,
            callback_data=f"ans_{test_index}_{q_num}_{i}" if highlight is None else "ignore"
        ))

    buttons.append(InlineKeyboardButton(text="Завершить тест", callback_data="finish"))
    rows = [buttons[i:i+2] for i in range(0, len(buttons)-1, 2)]
    rows.append([buttons[-1]])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_results(uid: int) -> str:
    d = user_data[uid]
    test_index = d["test_index"]
    q_list = tests[test_index]["questions"]
    total = len(q_list)
    percent = d["score"] / total * 100

    text = f"<b>Тест '{tests[test_index]['name']}' завершён!</b>\n\n"
    text += f"Правильных: <b>{d['score']}</b> из <b>{total}</b> ({percent:.1f}%)\n\n"

    # Правильные ответы
    corrects = [a for a in d["answers"] if a["chosen"] == a["correct"]]
    if corrects:
        text += "<b>Правильные ответы:</b>\n"
        for c in corrects:
            qn = c["q"] + 1
            chosen = q_list[c["q"]]["opts"][c["chosen"]]
            short_q = q_list[c["q"]]["q"].split("\n", 1)[1][:80] if "\n" in q_list[c["q"]]["q"] else q_list[c["q"]]["q"]
            text += f"<b>{qn}.</b> {short_q}…\n"
            text += f"   Вы: 🟩 <b>{chosen}</b>\n\n"

    # Ошибки
    errors = [a for a in d["answers"] if a["chosen"] != a["correct"]]
    if errors:
        text += "<b>Ошибки:</b>\n"
        for e in errors:
            qn = e["q"] + 1
            chosen = q_list[e["q"]]["opts"][e["chosen"]]
            correct = q_list[e["q"]]["opts"][e["correct"]]
            short_q = q_list[e["q"]]["q"].split("\n", 1)[1][:80] if "\n" in q_list[e["q"]]["q"] else q_list[e["q"]]["q"]
            text += f"<b>{qn}.</b> {short_q}…\n"
            text += f"   Вы: 🟥 {chosen}\n"
            text += f"   Правильно: 🟩 <b>{correct}</b>\n\n"
    else:
        text += "Ошибок нет — вы гений!\n"

    text += "\n/start — выбрать тест заново"
    return text

@dp.message(Command("start"))
async def start(message):
    uid = message.from_user.id
    user_data[uid] = {"current": 0, "score": 0, "answers": [], "test_index": None}
    await message.answer("Выберите тест:", reply_markup=get_test_keyboard())

@dp.callback_query(lambda c: c.data.startswith("start_test_"))
async def start_test(callback):
    uid = callback.from_user.id
    if uid not in user_data:
        return

    test_index = int(callback.data.split("_")[-1])
    user_data[uid] = {"current": 0, "score": 0, "answers": [], "test_index": test_index}
    q_list = tests[test_index]["questions"]
    await callback.message.edit_text(f"{tests[test_index]['name']} — 50 вопросов\n\n" + q_list[0]["q"], reply_markup=get_keyboard(test_index, 0))

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

    _, test_index_str, q_num_str, choice_str = callback.data.split("_")
    test_index = int(test_index_str)
    q_num = int(q_num_str)
    choice = int(choice_str)
    q_list = tests[test_index]["questions"]
    correct = q_list[q_num]["correct"]

    user_data[uid]["answers"].append({"q": q_num, "chosen": choice, "correct": correct})
    if choice == correct:
        user_data[uid]["score"] += 1

    # Подсветка
    await callback.message.edit_reply_markup(reply_markup=get_keyboard(test_index, q_num, highlight=choice))

    await asyncio.sleep(1.8)

    user_data[uid]["current"] += 1
    next_q = user_data[uid]["current"]

    if next_q >= len(q_list):
        await callback.message.edit_text(get_results(uid), reply_markup=None)
        del user_data[uid]
    else:
        await callback.message.edit_text(
            q_list[next_q]["q"],
            reply_markup=get_keyboard(test_index, next_q)
        )

async def main():
    print("Бот запущен — с выбором тестов, правильными ответами и квадратами!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())