import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv
from db import init_db
from utils import START_MENU, HELP_MENU, GET_NAME_TEXT
from utils import main_menu_keyboard, tasks_keyboard
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from db import get_user_by_telegram_id, add_user, get_all_users
from db import add_task, get_user_tasks, delete_task, mark_task_done
from db import get_done_tasks_today, get_user_count, get_rank, get_total_done_tasks
from db import get_task_by_id, get_user_done_tasks_today
from db import get_last_message_id, set_last_message_id

# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date

# from apscheduler.schedulers.asyncio import AsyncIOScheduler


init_db()
load_dotenv()

ADMIN = int(os.getenv("ADMIN"))
API_KEY = os.getenv("API_KEY")
bot = Bot(API_KEY)
dp = Dispatcher()


class RegisterState(StatesGroup):
    waiting_for_name = State()


# async def daily_job(bot):
#     # today_str = date.today().isoformat()
#     today_str = now_tehran.date().isoformat()

#     users = get_all_users()

#     for telegram_id in users:
#         tasks = get_user_done_tasks_today(telegram_id)

#         if not tasks:
#             continue

#         task_lines = [f"✅ {task['title']}" for task in tasks]
#         total_smiles = sum(task["priority"] for task in tasks)

#         message_text = (
#             f"🗒 گزارش امروز: {today_str}\n\n"
#             + "\n".join(task_lines)
#             + f"\n\n🙂 تعداد لبخندهای امروز: {total_smiles}"
#         )

#         try:
#             await bot.send_message(chat_id=telegram_id, text=message_text)
#         except Exception as e:
#             print(f"Error in sending message to {telegram_id}: {e}")


async def start_handler(pm: Message):
    await pm.answer(START_MENU, reply_markup=main_menu_keyboard())


async def help_handler(pm: Message):
    await pm.answer(
        HELP_MENU,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


async def register_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)

    if user:
        await message.answer("شما قبلا ثبت نام کردی!")
    else:
        await message.answer(GET_NAME_TEXT)
        await state.set_state(RegisterState.waiting_for_name)


async def register_name_handler(message: Message, state: FSMContext):
    name = message.text.strip()
    telegram_id = message.from_user.id

    add_user(telegram_id, name)

    await message.answer("اکانت شما ساخته شد ✅", reply_markup=main_menu_keyboard())
    await state.clear()


async def task_handler(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    if not message.text:
        return

    lines = [l.strip() for l in message.text.strip().splitlines() if l.strip()]

    # ❗ فقط دو حالت مجاز: 2 خط یا 3 خط
    if len(lines) not in (2, 3):
        await message.answer(
            "فرمت درست:\n\n"
            "تیتر\n#دسته‌بندی (اختیاری)\nعدد اولویت (1 تا 3)\n\n"
            "یا بدون دسته‌بندی:\nتیتر\nعدد اولویت"
        )
        return

    title = lines[0]

    # 🔹 اگر 2 خط بود → دسته‌بندی نامشخص
    if len(lines) == 2:
        category = "نامشخص"
        priority_num = lines[1]

    # 🔹 اگر 3 خط بود → بررسی هشتگ
    else:
        category_line = lines[1]
        priority_num = lines[2]

        hashtags = [word for word in category_line.split() if word.startswith("#")]

        if len(hashtags) != 1:
            await message.answer(
                "اگر دسته‌بندی می‌نویسی باید دقیقا یک هشتگ باشد\nمثال:\n#کدنویسی"
            )
            return

        category = hashtags[0][1:]

    # ✅ اعتبارسنجی اولویت
    priority_map = {"1": "معمولی", "2": "مهم", "3": "فوری"}
    if priority_num not in priority_map:
        await message.answer("عدد اولویت باید 1، 2 یا 3 باشد")
        return

    priority_text = priority_map[priority_num]

    success = add_task(message.from_user.id, title, category, priority_num)

    if not success:
        await message.answer("خطا: کاربر پیدا نشد. لطفا ابتدا /start بزنید.")
        return

    await message.answer(
        f"کار شما با دسته‌بندی {category} و اولویت {priority_text} ثبت شد ✅",
        reply_markup=main_menu_keyboard(),
    )


# async def tasks_handler(message: Message):
#     telegram_id = message.from_user.id

#     user = get_user_by_telegram_id(telegram_id)
#     if not user:
#         await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
#         return

#     tasks = get_user_tasks(telegram_id, only_pending=True)
#     if not tasks:
#         await message.answer("هیچ تسک انجام‌نشده‌ای پیدا نشد ✅")
#         return

#     for task in tasks:
#         task_id, title, category, priority = (
#             task["id"],
#             task["title"],
#             task["category"],
#             task["priority"],
#         )

#         keyboard = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [
#                     InlineKeyboardButton(
#                         text="✅ انجام دادن", callback_data=f"done:{task_id}"
#                     ),
#                     InlineKeyboardButton(
#                         text="🗑️ حذف", callback_data=f"delete:{task_id}"
#                     ),
#                 ]
#             ]
#         )

#         priority_map = {"1": "معمولی", "2": "مهم", "3": "فوری"}
#         priority_text = priority_map.get(str(priority), "نامشخص")

#         await message.answer(
#             f"📝 {title}\n#دسته‌بندی: {category}\n⚡ اولویت: {priority_text}",
#             reply_markup=keyboard,
#         )


# async def tasks_handler(message: Message):
#     telegram_id = message.from_user.id

#     user = get_user_by_telegram_id(telegram_id)
#     if not user:
#         await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
#         return

#     tasks = get_user_tasks(telegram_id, only_pending=True)
#     if not tasks:
#         await message.answer("هیچ تسک انجام‌نشده‌ای پیدا نشد ✅")
#         return

#     text = "کارهای انجام نشده 👇"

#     await message.answer(text, reply_markup=tasks_keyboard(tasks))


async def tasks_handler(message: Message):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
        return

    tasks = get_user_tasks(telegram_id, only_pending=True)

    if not tasks:
        text = "هیچ تسک انجام‌نشده‌ای پیدا نشد ✅"
    else:
        text = "کارهای انجام نشده 👇"

    # 🔹 حذف پیام قبلی تسک‌ها
    last_msg_id = get_last_message_id(telegram_id, "tasks")
    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=telegram_id, message_id=last_msg_id
            )
        except:
            pass  # اگر قبلا پاک شده بود ارور نده

    # 🔹 ارسال پیام جدید
    if tasks:
        sent_msg = await message.answer(text, reply_markup=tasks_keyboard(tasks))
    else:
        sent_msg = await message.answer(text)

    # 🔹 ذخیره message_id
    set_last_message_id(telegram_id, "tasks", sent_msg.message_id)


# async def profile_handler(message: Message):
#     telegram_id = message.from_user.id

#     user = get_user_by_telegram_id(telegram_id)
#     if not user:
#         await message.answer("ابتدا /start بزن و ثبت نام کن 😅")
#         return

#     full_name = user[2]
#     join_date_str = user[4]
#     score = user[3]
#     rank = get_rank(score)

#     join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
#     days_passed = (datetime.now() - join_date).days

#     await message.answer(
#         f"👤 اسم شما: {full_name}\n"
#         f"📅 تاریخ عضویت: {join_date} ({days_passed} روز پیش)\n"
#         f"⭐ امتیاز: {score}\n"
#         f"🔰 لقب شما: {rank}"
#     )


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

    text = (
        f"👤 اسم شما: {full_name}\n"
        f"📅 تاریخ عضویت: {join_date} ({days_passed} روز پیش)\n"
        f"⭐ امتیاز: {score}\n"
        f"🔰 لقب شما: {rank}"
    )

    # 🔹 حذف پیام قبلی اگر وجود داشت
    last_msg_id = get_last_message_id(telegram_id, "profile")
    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=telegram_id, message_id=last_msg_id
            )
        except:
            pass  # اگر پاک نشد مشکلی نیست

    # 🔹 ارسال پیام جدید
    sent_msg = await message.answer(text)

    # 🔹 ذخیره message_id جدید
    set_last_message_id(telegram_id, "profile", sent_msg.message_id)


# async def task_callback_handler(callback: CallbackQuery):
#     data = callback.data
#     action, task_id_str = data.split(":")
#     task_id = int(task_id_str)

#     if action == "delete":
#         success = delete_task(task_id, callback.from_user.id)

#         if success:
#             await callback.answer(
#                 "🗑️ تسک حذف شد\n2 امتیاز از شما کم شد", show_alert=True
#             )
#             await callback.message.delete()  # پاک کردن پیام تسک
#         else:
#             await callback.answer("خطا در حذف تسک", show_alert=True)

#     elif action == "done":
#         success, msg = mark_task_done(task_id)

#         await callback.answer(msg, show_alert=True)

#         if success:
#             await callback.message.delete()  # پاک کردن پیام تسک


async def task_callback_handler(callback: CallbackQuery):
    data = callback.data

    # چون تو utils این فرمت رو داریم:
    # task_done_12
    # task_delete_12
    # task_open_12

    _, action, task_id_str = data.split("_")
    task_id = int(task_id_str)

    telegram_id = callback.from_user.id

    if action == "delete":
        success = delete_task(task_id, telegram_id)

        if success:
            await callback.answer(
                "🗑️ تسک حذف شد\n2 امتیاز از شما کم شد", show_alert=True
            )
        else:
            await callback.answer("خطا در حذف تسک", show_alert=True)
            return

    elif action == "done":
        success, msg = mark_task_done(task_id)
        await callback.answer(msg, show_alert=True)

        if not success:
            return

    elif action == "open":
        task = get_task_by_id(task_id)  # یه تابع ساده که title رو برگردونه
        if task:
            await callback.answer(task["title"])  # toast
        else:
            await callback.answer("تسک پیدا نشد", show_alert=True)

    # ✅ گرفتن لیست جدید بعد از تغییر
    tasks = get_user_tasks(telegram_id, only_pending=True)

    if not tasks:
        await callback.message.edit_text("هیچ تسک انجام‌نشده‌ای باقی نمانده 🎉")
        return

    # ✅ ریفرش پیام
    await callback.message.edit_text(
        "کارهای انجام نشده 👇", reply_markup=tasks_keyboard(tasks)
    )


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


# async def today_handler(message: Message):
#     telegram_id = message.from_user.id

#     tasks, total_smiles = get_done_tasks_today(telegram_id)

#     today_str = datetime.now().strftime("%Y-%m-%d")

#     if not tasks:
#         await message.answer(
#             f"گزارش امروز: {today_str}\nهیچ کار انجام شده‌ای وجود ندارد ✅",
#             reply_markup=main_menu_keyboard(),
#         )
#         return

#     tasks_text = "\n".join([f"✅ {title}" for title in tasks])

#     await message.answer(
#         f"🗒گزارش امروز: {today_str}\n\n{tasks_text}\n\n🙂تعداد لبخندهای امروز: {total_smiles}",
#         reply_markup=main_menu_keyboard(),
#     )


async def today_handler(message: Message):
    telegram_id = message.from_user.id

    tasks, total_smiles = get_done_tasks_today(telegram_id)
    today_str = datetime.now().strftime("%Y-%m-%d")

    if not tasks:
        text = f"گزارش امروز: {today_str}\nهیچ کار انجام شده‌ای وجود ندارد ✅"
    else:
        tasks_text = "\n".join([f"✅ {title}" for title in tasks])
        text = (
            f"🗒گزارش امروز: {today_str}\n\n"
            f"{tasks_text}\n\n"
            f"🙂تعداد لبخندهای امروز: {total_smiles}"
        )

    # 🔹 حذف پیام قبلی گزارش امروز
    last_msg_id = get_last_message_id(telegram_id, "today")
    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=telegram_id, message_id=last_msg_id
            )
        except:
            pass

    # 🔹 ارسال پیام جدید
    sent_msg = await message.answer(text, reply_markup=main_menu_keyboard())

    # 🔹 ذخیره message_id
    set_last_message_id(telegram_id, "today", sent_msg.message_id)


async def log_handler(message: Message):
    telegram_id = message.from_user.id

    if telegram_id != ADMIN:
        await message.answer("❌ فقط ادمین می‌تواند این فرمان را استفاده کند")
        return

    user_count = get_user_count()
    done_count = get_total_done_tasks()

    await message.answer(
        f"""
            📊 آمار بات

            👤 تعداد کاربران: {user_count}
            ✅ کل کارهای انجام شده: {done_count}
            """
    )


async def send_log_handler(message: Message):
    if message.from_user.id != ADMIN:
        await message.answer("⛔ شما دسترسی ندارید")
        return

    today_str = date.today().isoformat()
    users = get_all_users()

    sent_count = 0

    for telegram_id in users:
        tasks = get_user_done_tasks_today(telegram_id)

        if not tasks:
            continue

        task_lines = [f"✅ {task['title']}" for task in tasks]
        total_smiles = sum(task["priority"] for task in tasks)

        text = (
            f"خسته نباشید 🌱\n\n"
            f"🗒 گزارش امروز: {today_str}\n\n"
            + "\n".join(task_lines)
            + f"\n\n🙂 تعداد لبخندهای امروز: {total_smiles}"
        )

        try:
            await bot.send_message(chat_id=telegram_id, text=text)
            sent_count += 1
        except Exception as e:
            print(f"Error sending to {telegram_id}: {e}")

    await message.answer(f"✅ log for {sent_count} user sent")


async def main():
    dp.message.register(start_handler, CommandStart())
    dp.message.register(help_handler, Command("help"))
    dp.message.register(register_handler, Command("register"))
    dp.message.register(register_name_handler, RegisterState.waiting_for_name)
    dp.message.register(tasks_handler, Command("tasks"))
    dp.message.register(profile_handler, Command("profile"))
    dp.message.register(send_handler, Command("send"))
    dp.message.register(today_handler, Command("today"))
    dp.message.register(log_handler, Command("log"))
    dp.message.register(send_log_handler, Command("send_log"))

    dp.message.register(today_handler, F.text == "گزارش امروز")
    dp.message.register(profile_handler, F.text == "پروفایل شما")
    dp.message.register(tasks_handler, F.text == "کارهای انجام نشده")
    dp.message.register(help_handler, F.text == "راهنمایی")

    dp.message.register(task_handler)
    dp.callback_query.register(task_callback_handler)

    # scheduler.add_job(daily_job, "cron", hour=0, minute=25, kwargs={"bot": bot})
    # scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
