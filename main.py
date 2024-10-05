import logging
from aiogram import Bot, Dispatcher, Router, types, BaseMiddleware
from aiogram.types import InputFile, Message, BotCommand, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse
import os
from aiogram import F
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
import time
from typing import List
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



API_TOKEN = '7225190355:AAF0LBh52-VNeOuuyM-q4tLeY_BZQhYC0Bs'
WEBHOOK_PATH = '/webhook'
# gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --timeout 60

CHANNEL_USERNAME = '@bobcoinhome'
WEB_APP_URL = "https://new-game-web-app.onrender.com"
# WEBHOOK_URL = f"https://b122-105-116-7-95.ngrok-free.app{WEBHOOK_PATH}"
WEBHOOK_URL = f"https://yusufbot-we1g.onrender.com{WEBHOOK_PATH}"

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
test_router = Router(name="test_router")
app = FastAPI()
security = HTTPBasic()



origins = [
    "https://gigbot.onrender.com",
    "https://tg-web-app-94sx.onrender.com"
    "http://localhost:5500",  # Add the origin of your HTML file
    "http://127.0.0.1:5500",
    "http://localhost:5173",  # Add the origin of your HTML file
    "http://127.0.0.1:5173",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    db_url="postgres://bobcoingame:@TYDev@2024@POST@postgresql-bobcoingame.alwaysdata.net:5432/bobcoingame_db2",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)



DUMMY_USERS = {
    
    "bobcoinapi": "bobcoin@#1234",

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

def get_current_uname(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "bobcoinapi"
    correct_password = "bobcoin@#1234"
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


#View all Tasks
@app.get("/donetasks")
async def getdone_tasks(current_user: str = Depends(get_current_user)):
    return await CompletedTask.all()

@app.post("/donetasks")
async def adddone_task(user_id: int =  Form(...), task_id: int = Form(...), current_user: str = Depends(get_current_user)):
    try:
        tasktt = await Tasks.get(id=task_id)
        userr = await User.get(id=user_id)
        confirm = await CompletedTask.filter(user=userr, task=tasktt)
        if confirm:
            raise HTTPException(status_code=404, detail="Already exists!!")
        else:
            task = await CompletedTask.create(user = userr, task = tasktt)
            return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")


@app.get("/donetasks/{user_id}/")
async def getdone_task(user_id: int, current_user: str = Depends(get_current_user)):
    try:
        task = await CompletedTask.filter(user_id=user_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")


@app.get("/tasks")
async def get_tasks(current_user: str = Depends(get_current_user)):
    return await Tasks.all()

#Get a specific task
@app.get("/task/{task_id}/")
async def get_task(task_id: int, current_user: str = Depends(get_current_user)):
    try:
        task = await Tasks.get(id=task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
 
 #Create a new task
@app.post("/tasks/")
async def add_task(detail: str =  Form(...), pts: int =  Form(...), link: str = Form(...), current_user: str = Depends(get_current_uname)):
    try:
        task = await Tasks.create(detail=detail, link=link, pts=pts)
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not created")

class TaskUpdate(BaseModel):
    deet: Optional[str] = None
    leenk: Optional[str] = None

@app.patch("/task/{task_id}/")
async def patch_task(task_id: int, task_update: TaskUpdate, current_user: str = Depends(get_current_uname)):
    try:
        task = await Tasks.get(id=task_id)
        if task_update.deet is not None:
            task.detail = task_update.deet
        if task_update.leenk is not None:
            task.link = task_update.leenk
        await task.save()
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")
#Edit a task
@app.put("/task/{task_id}/")
async def edit_task(task_id: int, deet: str = Form(...), leenk: str = Form(...), current_user: str = Depends(get_current_uname)):
    try:
        task = await Tasks.get(id=task_id)
        task.link = leenk
        task.detail = deet
        await task.save()
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")



@app.delete("/tasks/{task_id}/")
async def delete_task(task_id: int, current_user: str = Depends(get_current_uname)):
    task = await Tasks.get(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await task.delete()
    return {"detail": "Task deleted successfully"}


def only_numbers(s: str) -> str:
    return ''.join(filter(str.isdigit, s))

async def handle_referral(message: types.Message, bot: Bot):
    referrer_id = only_numbers(str(message.text)[7:])

    if referrer_id:
        await Frens.create(referrer_id=referrer_id, referred=message.from_user.id)
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


texte = """Hello! Welcome to Bobsquare  game.
You are now the director of a crypto exchange.
Tap the screen to play the rabbit race, tap to jump, pick up the carrot to increase your speed.
Join in the race to increase your earning and have a great passive income 
We’ll definitely appreciate your efforts once the token is listed (the dates are coming soon).
Don't forget about your friends — bring them to the game and get even more coins together!"""

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

@test_router.callback_query(lambda c: c.data == "bot_features")
async def taskmenu_back_callback(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Just keep tapping to avoid obstacles and the monster. Don't forget to play in lanscape mode ✍️🎮💥")




# Start command handler


@dp.message(Command('start'))
async def start(message: types.Message):

    keyboardifiok = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Play in 1 click", web_app=WebAppInfo(url=f'{WEB_APP_URL}?user={message.from_user.id}'))],
        [InlineKeyboardButton(text="Subscribe to channel", url="https://t.me/bobmemecoin")],
        [InlineKeyboardButton(text="How to earn from the game", callback_data="bot_features")],
        ],
        resize_keyboard=True)
    
    user = await User.filter(telegram_id=message.from_user.id).first()
    if user != None:
        logging.info('User Exists')
        await message.reply(texte, reply_markup=keyboardifiok)
        await message.answer("🎮🎯", reply_markup=menu_keyboard())
    else:
        await handle_referral(message, bot)
        await message.reply(texte, reply_markup=keyboardifiok)
        await message.answer("🎮🎯", reply_markup=menu_keyboard())
        
    

# Option handlers
@dp.message(lambda message: message.text == "Referral 🎉")
async def option1(message: types.Message):
    user_id = message.from_user.id
    ref_bal = await User.filter(telegram_id=message.from_user.id)
    if len(ref_bal) > 0: 
        ref = (ref_bal[0].referral_count)
        referral_link = f"https://t.me/singerrinderbot?start={user_id}"
        await message.reply(f"Your Total referrals: {ref}\n Your referral link:\n{referral_link}")
    else:
        referral_link = f"https://t.me/singerrinderbot?start={user_id}"
        await message.reply(f"Your referral link:\n{referral_link}")


@dp.message(lambda message: message.text == "Play Game 🎮")
async def option3(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Game", web_app=WebAppInfo(url=f'{WEB_APP_URL}?user={message.from_user.id}'))]
    ])
    await message.answer("Please click the button below to launch the web app.", reply_markup=keyboard)


@app.get("/")
def main_web_handler():
    return {"message": "Everything Okay!"}


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
    {"detail": "Task 1", "link": "https://example.com/task1"},
    {"detail": "Task 2", "link": "https://example.com/task2"},
    {"detail": "Task 3", "link": "https://example.com/task3"},
    {"detail": "Task 4", "link": "https://example.com/task4"},
    {"detail": "Task 5", "link": "https://example.com/task5"},
    {"detail": "Task 6", "link": "https://example.com/task6"},
    {"detail": "Task 7", "link": "https://example.com/task7"},
    {"detail": "Task 8", "link": "https://example.com/task8"},
    {"detail": "Task 9", "link": "https://example.com/task9"},
]

async def addtask():
    for task in tasks_data:
        await Tasks.create(detail=task['detail'], link=task['link'], pts=10)
        

# Webhook endpoint
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = await request.json()
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return JSONResponse(content={"ok": True})

@app.get("/frens")
async def get_frens(current_user: str = Depends(get_current_user)):
    return await Frens.all()


@app.get("/frens/{user_id}/")
async def get_fren(user_id: int, current_user: str = Depends(get_current_user)):
    try:
        user = await Frens.filter(referrer_id=user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"e no dey, not found")
 


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
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook set")
    dp.include_router(test_router)
    # await addtask()

    # Set bot commands
    commands = [
        BotCommand(command="start", description="Start the bot")
    ]
    await bot.set_my_commands(commands)
    

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Shutting down")
    await bot.delete_webhook()
    logging.info("Webhook removed")

