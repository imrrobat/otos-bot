from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os

load_dotenv()
ADMIN = int(os.getenv("ADMIN"))


def tasks_keyboard(tasks):
    builder = InlineKeyboardBuilder()

    for task in tasks:
        builder.row(
            InlineKeyboardButton(
                text=task["title"], callback_data=f"task_open_{task['id']}"
            )
        )
        builder.row(
            InlineKeyboardButton(text="✅", callback_data=f"task_done_{task['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"task_delete_{task['id']}"),
        )

    return builder.as_markup()


# def main_menu_keyboard():
#     keyboard = ReplyKeyboardMarkup(
#         keyboard=[
#             [KeyboardButton(text="گزارش امروز")],
#             [KeyboardButton(text="پروفایل شما")],
#             [KeyboardButton(text="کارهای انجام نشده")],
#             [KeyboardButton(text="گزارش ماه")],
#             [KeyboardButton(text="راهنمایی")],
#         ],
#         resize_keyboard=True,
#     )
#     return keyboard


def main_menu_keyboard(telegram_id: int):
    keyboard_buttons = [
        [KeyboardButton(text="گزارش امروز")],
        [KeyboardButton(text="پروفایل شما")],
        [KeyboardButton(text="کارهای انجام نشده")],
        [KeyboardButton(text="گزارش ماه")],
        [KeyboardButton(text="راهنمایی")],
    ]

    # 🔹 دکمه‌های مخصوص ادمین
    if telegram_id == ADMIN:
        keyboard_buttons.append([KeyboardButton(text="ارسال گزارش روز")])
        keyboard_buttons.append([KeyboardButton(text="آمار کلی کاربران")])
        keyboard_buttons.append([KeyboardButton(text="چک کردن")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True,
    )


START_MENU = """
سلام کاربرگرامی به OTOS خوش آمدین 🌱 
تو دو لیست شخصی شما  یک تسک - یک لبخند 🗒🙂
برای ثبت‌نام /register و برای راهنمایی /help را بفرستین.
"""

HELP_MENU = """
⚠️ برای افزودن کار جدید، کارتان را با این قالب بفرستید:
تیتر
#دسته‌بندی
عدد اولویت (1 تا 3)

برای نمایش گزارش امروز /today رو بزنید
برای دیدن کارها /tasks رو بزنید

برنامه‌نویس: علی حیدری (آقای ربات) ❤️
برای حمایت از این برنامه میتونید از لینک زیر برام یه کافی بخرین! 
https://www.coffeebede.com/mrrobat
"""

GET_NAME_TEXT = """
اسمتون رو وارد کنید ✨
این اسم توی پنل شخصی‌تون و توی رتبه‌بندی‌ها دیده میشه.
"""
