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


async def add_handler(pm: Message, com: CommandObject):
    task = com.args

    if not task:
        await pm.answer("اسم یه تسک رو وارد کن")
        return

    await pm.answer(f"پس تو میخوای کار {task} رو انجام بدی")


async def main():
    bot = Bot(API_KEY)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart)
    dp.message.register(help_handler, Command("help"))
    dp.message.register(add_handler, Command("add"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
