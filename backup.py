import logging
from aiogram import Bot, Dispatcher, Router, types, BaseMiddleware
from aiogram.types import InputFile, Message, BotCommand, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
import os
from aiogram import F
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
import time
import random
from connectToDatabase import connectToDatabase
from models import *
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise


from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

from aiogram_widgets.pagination import KeyboardPaginator


API_TOKEN = '7073143085:AAHOxWmJ20-hVEZQCydVhSCIShgEU7PO4Ms'
WEBHOOK_PATH = '/webhook'
# gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --timeout 60

CHANNEL_USERNAME = '@bobcoinhome'
WEB_APP_URL = 'https://gigbot.onrender.com'
WEBHOOK_URL = f"https://c079-105-112-214-150.ngrok-free.app{WEBHOOK_PATH}"
# WEBHOOK_URL = f"https://zigbot.onrender.com{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)

class MembershipMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def __call__(self, handler, event: Message, data: dict):
        # Check if the message is the /start command
        if event.text and event.text.startswith('/start'):
            return await handler(event, data)

        member = await self.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=event.from_user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            await event.answer(f"You need to join the channel first: https://t.me/{CHANNEL_USERNAME.lstrip('@')}")
        else:
            return await handler(event, data)



# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()
test_router = Router(name="test_router")


origins = [
    "https://gigbot.onrender.com",
    "http://localhost:5500",  # Add the origin of your HTML file
    "http://127.0.0.1:5500",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    db_url="sqlite://db_bot.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


def only_numbers(s: str) -> str:
    return ''.join(filter(str.isdigit, s))

async def handle_referral(message: types.Message, bot: Bot):
    referrer_id = only_numbers(str(message.text)[7:])

    if referrer_id:
        logging.info(f"Referrer ID: {referrer_id}")
        try:
            referrer = await User.get(telegram_id=str(referrer_id))
            #Check if the referrer's TG id is not equal to the Id of the user sending the message
            if str(referrer.telegram_id) != str(message.from_user.id):
                referrer.referral_count += 1
                await referrer.save()
                await User.create(telegram_id=message.from_user.id, gamepts=0, referral_count=0)

                ref_bal = await User.filter(telegram_id=str(referrer_id))
                ref = (ref_bal[0].referral_count)
                await bot.send_message(referrer.telegram_id, "You have received A Referral! You have referred a total of " + str(ref) + " Users")
                logging.info('User has been created, with existing referral')
            else:
                logging.info('Users cannot refer themselves')
        except Exception as e:
            logging.error(f"Referrer does not exist or referral has been done already start the bot using the normal command via the menu bar: {e}")
    else:
        await User.create(telegram_id=message.from_user.id, gamepts=0, referral_count=0)
        logging.info('User has been created')

async def create_user(telegram_id, gamepts):
    await User.create(telegram_id=telegram_id, gamepts=gamepts)


# dp.message.middleware(MembershipMiddleware(bot))

def menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Referral 🎉")],
            [KeyboardButton(text="Play Game 🎮")]
        ],
        resize_keyboard=True
    )
    return keyboard

def admin_menu_keyboard():
    keyboard1 = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Referral 🎉")],
            [KeyboardButton(text="Play Game 🎮")],
            [KeyboardButton(text="Tasks")],
        ],
        resize_keyboard=True
    )
    return keyboard1


# Start command handler
@dp.message(Command('start'))
async def start(message: types.Message):
    
    user = await User.filter(telegram_id=message.from_user.id).first()
    if user != None:
        logging.info('User Exists')
        await message.answer_photo(
        types.FSInputFile(path='fg.png'), caption="Use the higlighted icon to interact with bot")
    else:
        await handle_referral(message, bot)
        await message.answer_photo(
        types.FSInputFile(path='fg.png'), caption="Use the higlighted icon to interact with bot")
        admin_ids = ['7225278348']
        if str(message.from_user.id) in admin_ids:
            await message.answer("🎯👋", reply_markup=admin_menu_keyboard())
        else:
            await message.answer("🎯👋", reply_markup=menu_keyboard())
    


dp.callback_query.middleware(CallbackAnswerMiddleware())


@test_router.message(Command("tasks"))
async def kb_additional_buttons(message: Message):

    tasks = await Tasks.all()
    tlength = len(tasks)
    max_length = min(len(tasks), tlength)

    buttons = [
        
        InlineKeyboardButton(text=tasks[i].detail, callback_data=f"button_{i}")
        for i in range(max_length)
    ]
    additional_buttons = [
        [
            InlineKeyboardButton(text="Go back 🔙", callback_data="go_back"),
            InlineKeyboardButton(text="Add New ➕", callback_data="add_new"),
        ]
    ]
    
    paginator = KeyboardPaginator(
        router=test_router,
        data=buttons,
        additional_buttons=additional_buttons,    
        per_page=5, 
        per_row=1
    )

    await message.answer(
        text="Keyboard pagination with additional buttons",
        reply_markup=paginator.as_markup(),
    )

@test_router.callback_query(lambda c: c.data and c.data.startswith("button_"))
async def task_detail_callback(callback_query: types.CallbackQuery):
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Return to Tasks", callback_data="menu"),
        InlineKeyboardButton(text="Edit Task", callback_data="edit"),]
    ])

    task_id = callback_query.data
    cb_int = int(task_id.lstrip('button_'))
    task = await Tasks.get(id=cb_int)
    detail_text = f"Task Detail: {task.detail}\nLink: {task.link}"
    await callback_query.message.edit_text("🎯🎮")
    await bot.send_message(callback_query.from_user.id, detail_text, reply_markup=keyboard)

@test_router.callback_query(lambda c: c.data == "menu")
async def taskmenu_back_callback(callback_query: types.CallbackQuery):
    # Replace 'user_id' with the ID of the user you want to send the command to
    await bot.send_message(callback_query.from_user.id, "/tasks")



@test_router.callback_query(lambda c: c.data == "go_back")
async def go_back_callback(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("🎮🎯")

# Option handlers
@dp.message(lambda message: message.text == "Referral 🎉")
async def option1(message: types.Message):
    user_id = message.from_user.id
    ref_bal = await User.filter(telegram_id=message.from_user.id)
    if len(ref_bal) > 0: 
        ref = (ref_bal[0].referral_count)
        referral_link = f"https://t.me/Bobbygamebot?start={user_id}"
        await message.reply(f"Your Total referrals: {ref}\n Your referral link:\n{referral_link}")
    else:
        referral_link = f"https://t.me/Bobbygamebot?start={user_id}"
        await message.reply(f"Your referral link:\n{referral_link}")


@dp.message(lambda message: message.text == "Play Game 🎮")
async def option3(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Game", web_app=WebAppInfo(url=f'https://gigbot.onrender.com?{message.from_user.id}'))]
    ])
    await message.answer("Please click the button below to launch the web app.", reply_markup=keyboard)


@app.get("/")
def main_web_handler():
    return {"message": "Everything Okay!"}

DUMMY_USERS = {
    "user1": "password1",
    "user2": "password2",
    "user3": "password3"
}

# Secret key to encode and decode the JWT tokens
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90000000

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# JWT Token creation function
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=90000000)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token validation function
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in DUMMY_USERS:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Token endpoint
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    if username not in DUMMY_USERS or DUMMY_USERS[username] != password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# Refresh token endpoint
@app.post("/refresh")
async def refresh_access_token(refresh_token: str = Form(...)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in DUMMY_USERS:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    new_refresh_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
tasks_data = [
    {"detail": "Task 1 🎯", "link": "https://example.com/task1"},
    {"detail": "Task 2 🎯", "link": "https://example.com/task2"},
    {"detail": "Task 3 🎯", "link": "https://example.com/task3"},
    {"detail": "Task 4 🎯", "link": "https://example.com/task4"},
    {"detail": "Task 5 🎯", "link": "https://example.com/task5"},
    {"detail": "Task 6 🎯", "link": "https://example.com/task6"},
    {"detail": "Task 7 🎯", "link": "https://example.com/task7"},
    {"detail": "Task 8 🎯", "link": "https://example.com/task8"},
    {"detail": "Task 9 🎯", "link": "https://example.com/task9"},
    {"detail": "Task 10 🎯", "link": "https://example.com/task10"},
    {"detail": "Task 11 🎯", "link": "https://example.com/task11"},
    {"detail": "Task 12 🎯", "link": "https://example.com/task12"},
    {"detail": "Task 13 🎯", "link": "https://example.com/task13"},
    {"detail": "Task 14 🎯", "link": "https://example.com/task14"},
    {"detail": "Task 15 🎯", "link": "https://example.com/task15"},
    {"detail": "Task 16 🎯", "link": "https://example.com/task16"},
    {"detail": "Task 17 🎯", "link": "https://example.com/task17"},
    {"detail": "Task 18 🎯", "link": "https://example.com/task18"},
    {"detail": "Task 19 🎯", "link": "https://example.com/task19"},
    {"detail": "Task 20 🎯", "link": "https://example.com/task20"},
    {"detail": "Task 21 🎯", "link": "https://example.com/task21"},
    {"detail": "Task 22 🎯", "link": "https://example.com/task22"},
    {"detail": "Task 23 🎯", "link": "https://example.com/task23"},
    {"detail": "Task 24 🎯", "link": "https://example.com/task24"},
    {"detail": "Task 25 🎯", "link": "https://example.com/task25"},
    {"detail": "Task 26 🎯", "link": "https://example.com/task26"},
    {"detail": "Task 27 🎯", "link": "https://example.com/task27"},
    {"detail": "Task 28 🎯", "link": "https://example.com/task28"},
    {"detail": "Task 29 🎯", "link": "https://example.com/task29"},
    {"detail": "Task 30 🎯", "link": "https://example.com/task30"}
]


async def addtask():
    for task in tasks_data:
        await Tasks.create(detail=task['detail'], link=task['link'])
        

# Webhook endpoint
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = await request.json()
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return JSONResponse(content={"ok": True})


@app.get("/users")
# async def get_users():
async def get_users(current_user: str = Depends(get_current_user)):
    return await User.all()


@app.get("/user/{user_id}/")
async def get_gamepts(user_id: int, current_user: str = Depends(get_current_user)):
    try:
        user = await User.get(telegram_id=user_id)
        return user.gamepts
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
 

@app.put("/user/{user_id}/gamepts")
# async def update_gamepts(user_id: int, gamepts: int = Form(...)):
async def update_gamepts(user_id: int, gamepts: int = Form(...), current_user: str = Depends(get_current_user)):
    try:
        user = await User.get(telegram_id=user_id)
        user.gamepts += gamepts
        await user.save()
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")



@app.on_event("startup")
async def on_startup():
    await connectToDatabase()
    await addtask()
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook set")

    # Set bot commands
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="tasks", description="View Tasks")
    ]
    await bot.set_my_commands(commands)
    dp.include_router(test_router)

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Shutting down")
    await bot.delete_webhook()
    logging.info("Webhook removed")

