# bot.py
import asyncio
import os
import sys
import psutil
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ──────── Импорты проекта ────────
from questions import questions
from questions2 import questions2
from test_logic import init_tests, get_test_keyboard, get_question_keyboard, get_results
from logger import log_user_action, logger

# ──────── Токен ────────
BOT_TOKEN = "8397130065:AAGDA4or6syVF_q_qrNkxJwgihrIR-f_oYk"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ──────── Список тестов ────────
tests = [
    {"name": "АНГ 25.04 (копия)", "questions": questions},
    {"name": "Сливтер жинағы 24.03.2025", "questions": questions2},
]
init_tests(tests)

# Хранилище данных пользователей
user_data: dict[int, dict] = {}   # uid → {data, user_id, username}


# ──────── Защита от двойного запуска ────────
def is_bot_already_running() -> bool:
    current_pid = os.getpid()
    current_cmd = " ".join(sys.argv)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] and 'python' in proc.info['name'].lower():
            cmd = proc.info['cmdline']
            if cmd and len(cmd) > 1 and 'bot.py' in " ".join(cmd):
                if proc.info['pid'] != current_pid:
                    return True
    return False


# ──────── /start ────────
@dp.message(Command("start"))
async def start(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or "NoUsername"

    user_data[uid] = {
        "data": {"current": 0, "score": 0, "answers": [], "test_index": None},
        "user_id": uid,
        "username": username
    }

    log_user_action(uid, "START_COMMAND", f"Username: @{username}")
    await message.answer("Выберите тест:", reply_markup=get_test_keyboard())


# ──────── Старт теста ────────
@dp.callback_query(lambda c: c.data and c.data.startswith("start_test_"))
async def start_test(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        return

    test_index = int(callback.data.split("_")[-1])
    user_data[uid]["data"] = {"current": 0, "score": 0, "answers": [], "test_index": test_index}
    q_list = tests[test_index]["questions"]

    log_user_action(uid, "TEST_STARTED", f"Test: {tests[test_index]['name']}")

    await callback.message.edit_text(
        f"{tests[test_index]['name']} — {len(q_list)} вопросов\n\n{q_list[0]['q']}",
        reply_markup=get_question_keyboard(test_index, 0)
    )


# ──────── Обработка ответа ────────
@dp.callback_query(
    lambda c: c.data and (
        c.data.startswith("ans_") or
        c.data in ("finish", "ignore")
    )
)
async def process_answer(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        return

    data = user_data[uid]["data"]

    # ── Завершить тест ──
    if callback.data == "finish":
        await callback.message.edit_text(get_results(user_data[uid]), reply_markup=None)
        log_user_action(uid, "TEST_FINISHED_EARLY")
        del user_data[uid]
        return

    # ── Игнорировать уже подсвеченные кнопки ──
    if callback.data == "ignore":
        return

    # ── Проверка повторного ответа на тот же вопрос ──
    if callback.data.startswith("ans_"):
        _, test_idx_str, q_num_str, choice_str = callback.data.split("_")
        q_num = int(q_num_str)
        choice = int(choice_str)

        # Если уже отвечали – просто выходим
        if any(a["q"] == q_num for a in data["answers"]):
            return

        test_index = int(test_idx_str)
        q_list = tests[test_index]["questions"]
        correct = q_list[q_num]["correct"]

        # Сохраняем ответ
        data["answers"].append({"q": q_num, "chosen": choice, "correct": correct})
        if choice == correct:
            data["score"] += 1

        log_user_action(
            uid,
            "ANSWER",
            f"Q{q_num + 1}: {'Correct' if choice == correct else 'Wrong'} "
            f"(выбрано {choice}, правильно {correct})"
        )

        # Подсветка
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_question_keyboard(test_index, q_num, highlight=choice)
            )
        except Exception as e:
            # TelegramBadRequest: message is not modified → игнорируем
            if "not modified" not in str(e).lower():
                logger.exception("Ошибка при edit_reply_markup")

        await asyncio.sleep(1.8)

        # Переход к следующему вопросу
        data["current"] += 1
        next_q = data["current"]

        if next_q >= len(q_list):
            await callback.message.edit_text(get_results(user_data[uid]), reply_markup=None)
            del user_data[uid]
        else:
            await callback.message.edit_text(
                q_list[next_q]["q"],
                reply_markup=get_question_keyboard(test_index, next_q)
            )
        return


# ──────── Статистика (по желанию) ────────
@dp.message(Command("stats"))
async def stats(message: types.Message):
    if not user_data:
        await message.answer("Нет активных пользователей.")
        return

    text = "<b>Статистика:</b>\n\n"
    for uid, entry in user_data.items():
        d = entry["data"]
        if d["test_index"] is not None:
            total = len(tests[d["test_index"]]["questions"])
            percent = d["score"] / total * 100
            text += (
                f"• @{entry['username']} — {d['score']}/{total} "
                f"({percent:.0f}%)\n"
            )
    await message.answer(text)


# ──────── Запуск ────────
async def main():
    # Защита от двойного запуска
    if is_bot_already_running():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              "ОШИБКА: Бот уже запущен! Завершаю этот экземпляр.")
        return

    logger.info("Бот запущен — с логированием и модульной логикой!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Установите один раз: pip install aiogram psutil
    asyncio.run(main())