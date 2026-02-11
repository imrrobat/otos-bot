import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv
from db import init_db
from menu import START_MENU, HELP_MENU
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from db import get_user_by_telegram_id, add_user, get_all_users
from db import add_task, get_user_tasks, delete_task, mark_task_done
from db import get_done_tasks_today, get_user_count, get_rank
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


init_db()
load_dotenv()
API_KEY = os.getenv("API_KEY")
ADMIN = int(os.getenv("ADMIN"))


class RegisterState(StatesGroup):
    waiting_for_name = State()


async def start_handler(pm: Message):
    await pm.answer(START_MENU)


async def help_handler(pm: Message):
    await pm.answer(HELP_MENU)


async def register_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)

    if user:
        await message.answer("شما قبلا ثبت نام کردی!")
    else:
        await message.answer("تو رو با چی صدا کنم؟")
        await state.set_state(RegisterState.waiting_for_name)


async def register_name_handler(message: Message, state: FSMContext):
    name = message.text.strip()
    telegram_id = message.from_user.id

    add_user(telegram_id, name)

    await message.answer("اکانت شما ساخته شد ✅")
    await state.clear()


async def task_handler(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    lines = message.text.strip().splitlines()

    if len(lines) != 3:
        await message.answer(
            "لطفا پیام رو درست بفرستید:\nتیتر\n#دسته‌بندی\nعدد اولویت (1 تا 3)"
        )
        return

    title = lines[0].strip()
    category_line = lines[1].strip()
    priority_num = lines[2].strip()

    hashtags = [word for word in category_line.split() if word.startswith("#")]

    if len(hashtags) != 1:
        await message.answer("پیام شما باید دقیقا یک هشتگ داشته باشد. مثال:\n#کدنویسی")
        return

    category = hashtags[0][1:]

    success = add_task(message.from_user.id, title, category, priority_num)
    if not success:
        await message.answer("خطا: کاربر پیدا نشد. لطفا ابتدا /start بزنید.")
        return

    priority_map = {"1": "معمولی", "2": "مهم", "3": "فوری"}

    priority_text = priority_map.get(priority_num)
    if not priority_text:
        await message.answer("عدد اولویت باید 1، 2 یا 3 باشد")
        return

    await message.answer(
        f"کار شما با دسته‌بندی {category} و اولویت {priority_text} ثبت شد ✅"
    )


async def tasks_handler(message: Message):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
        return

    tasks = get_user_tasks(telegram_id, only_pending=True)
    if not tasks:
        await message.answer("هیچ تسک انجام‌نشده‌ای پیدا نشد ✅")
        return

    for task in tasks:
        task_id, title, category, priority = (
            task["id"],
            task["title"],
            task["category"],
            task["priority"],
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ انجام دادن", callback_data=f"done:{task_id}"
                    ),
                    InlineKeyboardButton(
                        text="🗑️ حذف", callback_data=f"delete:{task_id}"
                    ),
                ]
            ]
        )

        priority_map = {"1": "معمولی", "2": "مهم", "3": "فوری"}
        priority_text = priority_map.get(str(priority), "نامشخص")

        await message.answer(
            f"📝 {title}\n#دسته‌بندی: {category}\n⚡ اولویت: {priority_text}",
            reply_markup=keyboard,
        )


async def profile_handler(message: Message):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
        return

    full_name = user[2]
    join_date_str = user[4]
    score = user[3]
    rank = get_rank(score)

    join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
    days_passed = (datetime.now() - join_date).days

    await message.answer(
        f"👤 اسم شما: {full_name}\n"
        f"📅 تاریخ عضویت: {join_date} ({days_passed} روز پیش)\n"
        f"⭐ امتیاز: {score}\n"
        f"🔰 لقب شما: {rank}"
    )


async def task_callback_handler(callback: CallbackQuery):
    data = callback.data
    action, task_id_str = data.split(":")
    task_id = int(task_id_str)

    if action == "delete":
        success = delete_task(task_id, callback.from_user.id)

        if success:
            await callback.answer(
                "🗑️ تسک حذف شد\n2 امتیاز از شما کم شد", show_alert=True
            )
        else:
            await callback.answer("خطا در حذف تسک", show_alert=True)
    elif action == "done":
        success, msg = mark_task_done(task_id)
        await callback.answer(msg, show_alert=True)


async def send_handler(message: Message):
    if message.from_user.id != ADMIN:
        await message.answer("❌ فقط ادمین می‌تواند این پیام را ارسال کند")
        return

    text = message.text[len("/send") :].strip()
    if not text:
        await message.answer("❌ لطفا متن پیام را بعد از /send وارد کنید")
        return

    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await message.bot.send_message(chat_id=user_id, text=text)
            count += 1
        except:
            pass

    await message.answer(f"✅ پیام به {count} کاربر ارسال شد")


async def today_handler(message: Message):
    telegram_id = message.from_user.id

    tasks, total_priority = get_done_tasks_today(telegram_id)

    today_str = datetime.now().strftime("%Y-%m-%d")

    if not tasks:
        await message.answer(
            f"گزارش امروز: {today_str}\nهیچ کار انجام شده‌ای وجود ندارد ✅"
        )
        return

    tasks_text = "\n".join([f"✅ {title}" for title in tasks])

    await message.answer(
        f"گزارش امروز: {today_str}\n{tasks_text}\n\nتعداد لبخندهای امروز: {total_priority}"
    )


async def log_handler(message: Message):
    telegram_id = message.from_user.id

    if telegram_id != ADMIN:
        await message.answer("❌ فقط ادمین می‌تواند این فرمان را استفاده کند")
        return

    count = get_user_count()
    await message.answer(f"تعداد کاربران ثبت‌نام شده: {count}")


async def main():
    bot = Bot(API_KEY)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(help_handler, Command("help"))
    dp.message.register(register_handler, Command("register"))
    dp.message.register(register_name_handler, RegisterState.waiting_for_name)
    dp.message.register(tasks_handler, Command("tasks"))
    dp.message.register(profile_handler, Command("profile"))
    dp.message.register(send_handler, Command("send"))
    dp.message.register(today_handler, Command("today"))
    dp.message.register(log_handler, Command("log"))

    dp.message.register(task_handler)
    dp.callback_query.register(task_callback_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
