import asyncio
from calendar import c
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from db import (
    init_db,
    add_channel,
    remove_channel,
    get_all_channels,
    AsyncSessionLocal,
    Channel,
    add_filter,
    get_all_filters,
    remove_filter
)

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from kb import main_kb, channels_kb, channel_kb, filters_kb, filter_kb, back_to_filter_menu_kb, back_to_channel_menu_kb
from teleton_client import get_channel_info, leave_channel_listening, generate_all_case_forms, message_to_html_safe
import os
from dotenv import load_dotenv

load_dotenv()

# Вставь свои данные
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
GROUP_ID = os.getenv("GROUP_ID")
current_handler = None  # Храним текущий обработчик
CHANNELS = []  # Текущий список каналов для слежения

# --- Telethon клиент ---
telethon_client = TelegramClient('session_name', API_ID, API_HASH)

# --- Aiogram бот ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM States ---
class AddChannel(StatesGroup):
    waiting_for_id = State()

class FiltersChannels(StatesGroup):
    add_filter = State()

# --- Aiogram Handlers ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(text="Основное меню", reply_markup = await main_kb())
    

@dp.callback_query(F.data == "channels_info")
async def get_filters_info(callback: CallbackQuery):
    await callback.message.edit_text(text='Управление каналами', reply_markup = await channels_kb())


@dp.callback_query(F.data == "add_channel")
async def add_channel_fsm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите ID (число) или @username канала.')
    await state.set_state(AddChannel.waiting_for_id)

@dp.message(AddChannel.waiting_for_id)
async def add_channel_to_db(message: types.Message, state: FSMContext):
    text = str(message.text)
    if text.startswith('-') and text[1:].isdigit():
        channel_id = int(message.text)
        channel_username = await get_channel_info(channel_id_or_name=channel_id, phone_number=PHONE_NUMBER, client=telethon_client)
        if channel_username == False:
            await message.answer("Канал не найден")
            return
        channel_id = str(channel_id)
        
    elif text.startswith("@"):
        channel_username = message.text
        channel_id = await get_channel_info(channel_id_or_name=channel_username, phone_number=PHONE_NUMBER, client=telethon_client)
        if channel_id == False:
            await message.answer("Канал не найден")
            return
        channel_id = str(channel_id)
    else:
        await message.answer("Неверный формат! Введите ID (число) или @username канала.")
        return
    
    result = await add_channel(channel_id=channel_id, channel_name=channel_username)
    if result:
        await message.answer(text=f"{result}")
    else: 
        await message.answer(text='Канал добавлен')
        channels = await get_all_channels()
        channel_ids = []
        for channel in channels:
            channel_ids.append(channel.channel_id)
        await update_channels_and_restart_handler(new_channels=channel_ids)
    

    
    await message.answer(text='Укправление каналами', reply_markup = await channels_kb())
    await state.clear()


@dp.callback_query(F.data == "all_channels")
async def get_all_channels_from_db(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    message_ids = []
    channels = await get_all_channels()
    for channel in channels:
        a = await callback.message.answer(
            text=f'Название канала: {channel.channel_name} \nID канала: {channel.channel_id}',
            reply_markup= await channel_kb(id=channel.channel_id))
        message_ids.append(a.message_id)
    await callback.message.answer("Нажмите чтобы вернутся в меню", reply_markup=await back_to_channel_menu_kb())
    await state.update_data(message_ids=message_ids)
        

@dp.callback_query(F.data.startswith("delete_channel"))
async def get_filters_info(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await remove_channel(channel_id)
    await leave_channel_listening(channel_id=channel_id, phone_number=PHONE_NUMBER, client=telethon_client)
    await callback.message.delete()
    CHANNELS.remove(channel_id)
    await update_channels_and_restart_handler(CHANNELS)


@dp.callback_query(F.data == 'back_to_channel_menu')
async def back_to_сhannel_menu(callback: CallbackQuery, state: FSMContext, bot : Bot):
    await callback.message.delete()
    ids = await state.get_data()
    ids = ids.get('message_ids')
    try:
        for id in ids:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=id)
        await callback.message.answer("Управление каналами", reply_markup=await channels_kb())
    except:
        await callback.message.answer("Управление каналами", reply_markup=await channels_kb())
    await state.clear()

    



@dp.callback_query(F.data == 'filters_info')
async def reklama(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Управление фильтрами", reply_markup=await filters_kb())



@dp.callback_query(F.data == 'add_filter')
async def add_reklama(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите текст фильтра рекламы")
    await state.set_state(FiltersChannels.add_filter)


@dp.message(FiltersChannels.add_filter)
async def add_reklama_filter(message: types.Message, state: FSMContext):
    chek = await add_filter(filter_text=message.text)
    
    if chek:
        await message.answer("Такой фильтр уже существует")
        await asyncio.sleep(2)
        await message.delete()
        return
    await message.answer("Фильтр добавлен", reply_markup=await filters_kb())
    await state.clear()


@dp.callback_query(F.data == 'all_filters')
async def show_reklama(callback: CallbackQuery, state: FSMContext):
    filters = await get_all_filters()
    message_ids = []
    await callback.message.delete()
    for filter in filters:
        a = await callback.message.answer(filter.filter_text, reply_markup=await filter_kb(filter.id))
        message_ids.append(a.message_id)
    await callback.message.answer("Нажмите чтобы вернутся в меню", reply_markup=await back_to_filter_menu_kb())
    await state.update_data(message_ids=message_ids)



@dp.callback_query(F.data.startswith('delete_filter'))
async def delete_reklama(callback: CallbackQuery):
    filter_id = int(callback.data.split(":")[1])
    await remove_filter(id=filter_id)
    await callback.message.edit_text("Фильтр рекламы удален")
    await asyncio.sleep(1)
    await callback.message.delete()


@dp.callback_query(F.data == 'back_to_filter_menu')
async def back_to_filter_menu(callback: CallbackQuery, state: FSMContext, bot : Bot):
    await callback.message.delete()
    ids = await state.get_data()
    ids = ids.get('message_ids')
    try:
        for id in ids:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=id)
        await callback.message.answer("Управление фильтрами", reply_markup=await filters_kb())
    except:
        await callback.message.answer("Управление фильтрами", reply_markup=await filters_kb())
    await state.clear()






@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(text="Основное меню", reply_markup = await main_kb())





# --- Функция создания обработчика ---

async def register_handler():
    global current_handler

    if current_handler:
        telethon_client.remove_event_handler(current_handler)
        print("❌ Старый обработчик удалён")
    @telethon_client.on(events.NewMessage(chats=CHANNELS))
    async def new_channel_message_handler(event):
        chan = await event.get_chat()
        text = event.message.message or ""
        if not text:
            return
    # Если в сообщении есть медиа, то пытаемся получить caption
        
        

        
        text = text.lower().strip()
        data =  await get_all_filters()
        
        for phrase in data:
            phrase = phrase.filter_text
            
            case_forms = await generate_all_case_forms(phrase)  
            for i in case_forms:
                
                if i in text:
                    print('Фильтр найден')
                    return
        print("Фильтр не найден")
        entity = await telethon_client.get_entity(int(GROUP_ID)) 
        text = await message_to_html_safe(event.message)
        try:       
            await telethon_client.send_message(entity=entity, message=text, parse_mode='html')
        except:
            await telethon_client.send_message(entity=entity, message=text)
    
    
    current_handler = new_channel_message_handler
    print(f"✅ Новый обработчик событий зарегистрирован для {len(CHANNELS)} каналов")





# --- Функция обновления списка каналов ---

async def update_channels_and_restart_handler(new_channels):
    global CHANNELS
    CHANNELS = new_channels
    await register_handler()  



# --- Запуск всех задач ---
async def main():
    await init_db()
    await telethon_client.start(phone=PHONE_NUMBER)
    channels = await get_all_channels()
    channels = [channel.channel_id for channel in channels]
    print(channels)
    await update_channels_and_restart_handler(channels)
    # Запускаем Telethon клиента
    asyncio.create_task(telethon_client.run_until_disconnected())
    # Запускаем Aiogram бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())