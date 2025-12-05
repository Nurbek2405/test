# test_logic.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from logger import log_user_action

# Внешние данные (импортируются в bot.py)
tests = []

def init_tests(test_list):
    global tests
    tests = test_list

def get_test_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=test["name"], callback_data=f"start_test_{i}")
        for i, test in enumerate(tests)
    ]
    rows = [buttons[i:i+1] for i in range(0, len(buttons), 1)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_question_keyboard(test_index: int, q_num: int, highlight: int = None) -> InlineKeyboardMarkup:
    q_list = tests[test_index]["questions"]
    opts = q_list[q_num]["opts"]
    correct = q_list[q_num]["correct"]

    buttons = []
    for i, text in enumerate(opts):
        if not text.strip():
            continue
        prefix = ""
        if highlight is not None:
            if i == correct:
                prefix = "🟩 "
            elif i == highlight:
                prefix = "🟥 "
        btn_text = prefix + text
        callback = f"ans_{test_index}_{q_num}_{i}" if highlight is None else "ignore"
        buttons.append(InlineKeyboardButton(text=btn_text, callback_data=callback))

    buttons.append(InlineKeyboardButton(text="Завершить тест", callback_data="finish"))
    rows = [buttons[i:i+2] for i in range(0, len(buttons)-1, 2)]
    rows.append([buttons[-1]])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_results(user_data_entry) -> str:
    uid = user_data_entry["user_id"]
    d = user_data_entry["data"]
    test_index = d["test_index"]
    q_list = tests[test_index]["questions"]
    total = len(q_list)
    percent = d["score"] / total * 100

    log_user_action(uid, "TEST_COMPLETED", f"Score: {d['score']}/{total} ({percent:.1f}%)")

    text = f"<b>Тест '{tests[test_index]['name']}' завершён!</b>\n\n"
    text += f"Правильных: <b>{d['score']}</b> из <b>{total}</b> ({percent:.1f}%)\n\n"

    corrects = [a for a in d["answers"] if a["chosen"] == a["correct"]]
    errors = [a for a in d["answers"] if a["chosen"] != a["correct"]]

    if corrects:
        text += "<b>Правильные:</b>\n"
        for c in corrects:
            qn = c["q"] + 1
            chosen = q_list[c["q"]]["opts"][c["chosen"]]
            short_q = q_list[c["q"]]["q"].split("\n", 1)[1][:80]
            text += f"<b>{qn}.</b> {short_q}…\n   Вы: 🟩 <b>{chosen}</b>\n\n"

    if errors:
        text += "<b>Ошибки:</b>\n"
        for e in errors:
            qn = e["q"] + 1
            chosen = q_list[e["q"]]["opts"][e["chosen"]]
            correct = q_list[e["q"]]["opts"][e["correct"]]
            short_q = q_list[e["q"]]["q"].split("\n", 1)[1][:80]
            text += f"<b>{qn}.</b> {short_q}…\n"
            text += f"   Вы: 🟥 {chosen}\n"
            text += f"   Правильно: 🟩 <b>{correct}</b>\n\n"
    else:
        text += "Ошибок нет — вы гений!\n"

    text += "\n/start — выбрать тест заново"
    return text