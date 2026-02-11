import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, CommandObject
from config import API_KEY


async def start_handler(pm: Message):
    name = pm.from_user.full_name
    await pm.answer(f"سلام {name} عزیز")


async def help_handler(pm: Message):
    await pm.answer("به زودی در این مکان، هلپ نصب میشود")


async def task_handler(message: Message):
    # جدا کردن خطوط
    lines = message.text.strip().splitlines()

    if len(lines) != 3:
        await message.answer(
            "لطفا پیام رو درست بفرستید:\nتیتر\n#دسته‌بندی\nعدد اولویت (1 تا 3)"
        )
        return

    title = lines[0].strip()
    category_line = lines[1].strip()
    priority_num = lines[2].strip()

    # بررسی هشتگ
    hashtags = [word for word in category_line.split() if word.startswith("#")]

    if len(hashtags) != 1:
        await message.answer(
            "پیام شما باید دقیقا یک هشتگ داشته باشد. مثال:\n#سوپرمارکت"
        )
        return

    category = hashtags[0][1:]  # حذف # از اول

    # تبدیل اولویت عددی به متن
    priority_map = {"1": "معمولی", "2": "مهم", "3": "فوری"}

    priority_text = priority_map.get(priority_num)
    if not priority_text:
        await message.answer("عدد اولویت باید 1، 2 یا 3 باشد")
        return

    # پاسخ به کاربر
    await message.answer(
        f"کار شما با دسته‌بندی {category} و اولویت {priority_text} دریافت شد ✅"
    )


async def main():
    bot = Bot(API_KEY)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(help_handler, Command("help"))
    dp.message.register(task_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
