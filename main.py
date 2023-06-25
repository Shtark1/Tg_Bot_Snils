import datetime
import time
import re
import logging
import sqlite3

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


# ЗАПРОСЫ К БД С ПОЛЬЗОВАТЕЛЯМИ
class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id, username):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`, `username`, `day_reg`, `test_check`, `day_buy_sub`) VALUES (?, ?, ?, ?, ?)",
                                       (user_id, username, datetime.datetime.now(), 10, "У вас нет подписки"))

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def update_accept_conf(self, user_id, accept_conf_value):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `accept_conf` = ?, `day_accept_conf` = ? WHERE `user_id` = ?",
                                       (accept_conf_value, datetime.datetime.now(), user_id))

    def update_test_check(self, user_id):
        with self.connection:
            # Получить текущее значение test_check
            current_value = self.cursor.execute("SELECT `test_check` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchone()[0]

            # Вычесть 1 и обновить значение в базе данных
            new_value = current_value - 1
            self.cursor.execute("UPDATE `users` SET `test_check` = ? WHERE `user_id` = ?", (new_value, user_id))
            return new_value

    def select_test_check(self, user_id):
        with self.connection:
            # Получить текущее значение test_check
            current_value = self.cursor.execute("SELECT `test_check` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchone()[0]

            return current_value

    def select_profile(self, user_id):
        with self.connection:
            # Получить текущее значение test_check
            current_value = self.cursor.execute("SELECT `day_reg`, `test_check`, `day_buy_sub` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()[0]

            return current_value

    def set_time_sub(self, user_id, time_sub):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `day_buy_sub` = ? WHERE `user_id` = ?", (time_sub, user_id,))


db = Database('database')


# ЗАПРОСЫ К БД С ИНФО
def search(key_code):
    # Создаем соединение с базой данных
    conn = sqlite3.connect('dbmentions.db')
    cursor = conn.cursor()
    # Выполняем SELECT запрос для поиска строк с нужным кодом
    query = f"SELECT GUID, pub_date, dec_date FROM messages WHERE code LIKE '%{key_code}%'"
    result = cursor.execute(query).fetchall()
    if result:
        # Выводим найденные строки
        text = ['Вот что мне удалось найти:']
        for row in result:
            message_guid, pub_date, dec_date = row
            text = text + [f'''Дата публикации: {pub_date}
Дата подачи заявления: {dec_date}
Ссылка на сообщение: https://old.bankrot.fedresurs.ru/MessageWindow.aspx?ID={message_guid}&attempt=1''']
        cursor.close()
        conn.close()
        return text
    else:
        cursor.close()
        conn.close()
        return 'Совпадений с указанным ИНН/ОГРН/ОГРНИП/СНИЛС не найдено.'


# ДАННЫЕ ДЛЯ НАСТРОЙКИ
CONFIG = {
    "TOKEN": "",
    "ID_CHANNEL": ,
    "YOOPAYMENT": "",
    "PRICE_SUB": 12344  # целое число последние две цифры это копейки
}

# СООБЩЕНИЯ
MESSAGES = {
    "not_in_group": "Чтобы использовать бота, необходимо подписаться на канал @dawdawd231312.",
    "in_group": "Спасибо за подписку",
    "sms_not_in_group": "Вы не вступили в группу(",
    "policy_confirmation": "Необходимо ознакомиться с нашей политикой конфиденциальности.",
    "thanks": "Спасибо, что подтвердили нашу политику конфиденциальности.",
    "start": """Данный бот предназначен для поиска информации на федресурсе по ИНН/ОГРН/ОГРНИП/СНИЛС.
Сейчас у Вас есть 10 бесплатных проверок. Для снятия ограничений необходимо оформить платную подписку на бота. 
Доступ к основным функциям бота также можно получить из кентекстного меню, нажав кнопку справа от строки ввода сообщений.""",

    "input_inn": "Введите ИНН/ОГРН/ОГРНИП/СНИЛС длиной от 10 до 15 символов:",
    "no_input_inn": "Вы ввели не корректно\nВведите ИНН/ОГРН/ОГРНИП/СНИЛС длиной от 10 до 15 символов:",
    "not_command": "Такой команды нет(",
    "not_check": "У вас закончились пробные поиски\nМожете купить подписку для безлимитного поиска",
    "info_sub": "Информацияя о подписке",
}

# КНОПКИ
btn_check_prov = KeyboardButton("Сделать проверку")
btn_buy_sub = KeyboardButton("Купить подписку")
btn_profile = KeyboardButton("Профиль")
btn_cancel = KeyboardButton("Отмена")

btn_channel = InlineKeyboardButton(text="Подписаться", url=)
btn_accept_channel = InlineKeyboardButton(text="Я подисался", callback_data="check")

btn_polit = InlineKeyboardButton(text="Ознакомиться", url=)
btn_accept = InlineKeyboardButton("✅ Согласен ✅", callback_data="accept_pol")

BUTTON_TYPES = {
    "BTN_HOME": ReplyKeyboardMarkup(resize_keyboard=True).add(btn_check_prov).add(btn_buy_sub).add(btn_profile),
    "BTN_SUB": InlineKeyboardMarkup().add(btn_channel, btn_accept_channel),
    "BTN_POLIT": InlineKeyboardMarkup().add(btn_polit, btn_accept),
    "BTN_CANCEL": ReplyKeyboardMarkup(resize_keyboard=True).add(btn_cancel)
}


# СОСТОЯНИЯ
class StatesUSERS(Helper):
    mode = HelperMode.snake_case

    STATES_0 = ListItem()
    STATES_1 = ListItem()
    STATES_2 = ListItem()
    STATES_3 = ListItem()
    STATES_4 = ListItem()
    STATES_5 = ListItem()
    STATES_6 = ListItem()


logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG)

bot = Bot(token=CONFIG["TOKEN"])
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


# ===================================================
# =============== СТАНДАРТНЫЕ КОМАНДЫ ===============
# ===================================================
@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    #   ПРОВЕРКА ПОДПИСКИ НА КАНАЛ
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id, message.from_user.username)

    user_channel_status = await bot.get_chat_member(chat_id=CONFIG["ID_CHANNEL"], user_id=message.from_user.id)
    if user_channel_status["status"] != 'left':
        await message.answer(MESSAGES['start'], reply_markup=BUTTON_TYPES["BTN_HOME"])

    else:
        await bot.send_message(message.from_user.id, MESSAGES["not_in_group"], reply_markup=BUTTON_TYPES["BTN_SUB"])
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(StatesUSERS.all()[0])


# =================================================
# =============== ПРОВЕРКА ПОДПИСКИ ===============
# =================================================
@dp.message_handler(state=StatesUSERS.STATES_0)
async def check_sub(message: Message):
    state = dp.current_state(user=message.from_user.id)
    user_channel_status = await bot.get_chat_member(chat_id=CONFIG["ID_CHANNEL"], user_id=message.from_user.id)
    if user_channel_status["status"] != 'left':
        await message.answer(MESSAGES['in_group'])
        await message.answer(MESSAGES['policy_confirmation'], reply_markup=BUTTON_TYPES["BTN_POLIT"])
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(StatesUSERS.all()[1])

    else:
        await bot.send_message(message.from_user.id, MESSAGES["not_in_group"], reply_markup=BUTTON_TYPES["BTN_SUB"])
        await state.set_state(StatesUSERS.all()[0])


@dp.callback_query_handler(lambda callback: callback.data == "check", state=StatesUSERS.STATES_0)
async def check_sub_q(callback: CallbackQuery):
    user_channel_status = await bot.get_chat_member(chat_id=CONFIG["ID_CHANNEL"], user_id=callback.from_user.id)
    if user_channel_status["status"] != 'left':
        await callback.message.delete()
        await callback.message.answer(MESSAGES['in_group'])
        await callback.message.answer(MESSAGES['policy_confirmation'], reply_markup=BUTTON_TYPES["BTN_POLIT"])
        state = dp.current_state(user=callback.from_user.id)
        await state.set_state(StatesUSERS.all()[1])
    else:
        await callback.answer(MESSAGES["sms_not_in_group"], show_alert=True)


# =================================================
# =============== СОГЛАСИЕ КОНФИДЕЦ ===============
# =================================================
@dp.callback_query_handler(lambda callback: callback.data == "accept_pol", state=StatesUSERS.STATES_1)
async def check_sub_q(callback: CallbackQuery):
    db.update_accept_conf(callback.from_user.id, True)
    await callback.message.delete()
    await callback.message.answer(MESSAGES['thanks'])
    await callback.message.answer(MESSAGES['start'], reply_markup=BUTTON_TYPES["BTN_HOME"])
    state = dp.current_state(user=callback.from_user.id)
    await state.finish()


@dp.message_handler(state=StatesUSERS.STATES_1)
async def check_sub_q(message: Message):
    await message.answer(MESSAGES['policy_confirmation'], reply_markup=BUTTON_TYPES["BTN_POLIT"])
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(StatesUSERS.all()[1])


# =================================================
# ================ ПРОВЕРКА ДАННЫХ ================
# =================================================
@dp.message_handler(lambda message: message.text.lower() == 'сделать проверку')
async def check_prov(message: Message):
    if db.select_test_check(message.from_user.id) >= 1:
        await message.answer(MESSAGES['input_inn'], reply_markup=BUTTON_TYPES["BTN_CANCEL"])
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(StatesUSERS.all()[2])

    try:
        if time_sub_day(db.select_profile(message.from_user.id)[2]):
            await message.answer(MESSAGES['input_inn'], reply_markup=BUTTON_TYPES["BTN_CANCEL"])
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(StatesUSERS.all()[2])
    except:
        await message.answer(MESSAGES['not_check'], reply_markup=BUTTON_TYPES["BTN_HOME"])


# ================ ПОЛУЧЕНИЕ ВВЕДЁНЫХ ДАННЫХ ================
@dp.message_handler(state=StatesUSERS.STATES_2)
async def check_prov(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await message.answer(MESSAGES['start'], reply_markup=BUTTON_TYPES["BTN_HOME"])
        await state.finish()
    elif re.match(r'^\d{10,15}$', message.text):
        a = db.update_test_check(message.from_user.id)
        await message.answer(f"Успех!\nУ вас осталось {a} бесплатных проверок", reply_markup=BUTTON_TYPES["BTN_HOME"])
        # ищем данные в бд mentions
        all_info = search(message.text)
        for info in all_info:
            await message.answer(text=info, reply_markup=BUTTON_TYPES["BTN_HOME"])
        await state.finish() 
    else:
        await message.answer(MESSAGES['no_input_inn'], reply_markup=BUTTON_TYPES["BTN_CANCEL"])
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(StatesUSERS.all()[2])


# ==================================================
# ================ ПОКУПКА ПОДПИСКИ ================
# ==================================================
@dp.message_handler(lambda message: message.text.lower() == 'купить подписку')
async def check_prov(message: Message):
    # await message.answer(MESSAGES['info_sub'], reply_markup=BUTTON_TYPES["BTN_CANCEL"])
    label = "Описание"

    PRICE = LabeledPrice(label=label, amount=CONFIG["PRICE_SUB"])

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Тут 1",
        description="Тут 2",
        provider_token=CONFIG["YOOPAYMENT"],
        currency='RUB',
        prices=[PRICE],
        start_parameter='time-machine-example',
        payload=f"{message.message_id}",
    )


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


def time_sub_day(get_time):
    time_now = int(time.time())
    middle_time = int(get_time) - time_now

    if middle_time <= 0:
        return False
    else:
        dt = str(datetime.timedelta(seconds=middle_time))
        dt = dt.replace("days", "дней")
        dt = dt.replace("day", "день")
        return dt


def days_to_secons(days):
    return days * 24 * 60 * 60


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: Message):
    days = 30
    time_sub = int(time.time()) + days_to_secons(days)
    db.set_time_sub(message.from_user.id, time_sub)

    await bot.send_message(message.from_user.id, "Оплата прошла успешна!\nВам доступна подписка на месяц")


# ==================================================
# ===================== ПРОФИЛЬ ====================
# ==================================================
@dp.message_handler(lambda message: message.text.lower() == 'профиль')
async def check_prov(message: Message):
    info_prof = db.select_profile(message.from_user.id)
    try:
        user_sub = time_sub_day(info_prof[2])
    except:
        user_sub = "У вас нет подписки"
    await message.answer(f"Ваш id: {message.from_user.id}\nДата регестрации: {info_prof[0][0:10]}\nКол-во пробных поисков: {info_prof[1]}\nДо конца подписки осталось: {user_sub}")


# ===================================================
# =============== НЕИЗВЕСТНАЯ КОМАНДА ===============
# ===================================================
@dp.message_handler()
async def not_command(message: Message):
    await message.answer(MESSAGES['not_command'], reply_markup=BUTTON_TYPES["BTN_HOME"])


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
