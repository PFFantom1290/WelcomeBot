"""
TG-бот: доступ к меню только после анкеты
еженедельный «рандомный» топ в понедельник в 10:00
без зависимости от apscheduler
"""

import os
import random
import time
import asyncio
import logging
import datetime as dt

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# ─────────────────────────── CONFIG ────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv('WELCOME_BOT_TOKEN')
ADMIN_ID  = int(os.getenv('MY_ID'))

MAIN_CHANNEL_LINK     = "https://t.me/+NpcxCSbz0VxjMjMy"
PAYMENTS_CHANNEL_LINK = "https://t.me/+ojyK0KkEw-E4NDRi"
GROUP_CHAT_LINK       = "https://t.me/YourGroupChat"  # Замените на свой
CHILL_MANOFF_LINK     = "https://t.me/Chill_manoff"
WHAT_WE_DO_LINK       = "https://telegra.ph/Nashe-napravlenie-05-22"
ELECTRUM_SETUP_LINK   = "https://telegra.ph/Ustanovka-i-nastrojka-Electrum-05-23"
CANCEL_TX_LINK        = "https://telegra.ph/OTMENA-BTC-TRANZAKCII-05-31"
MANAGER_GUIDE_LINK    = "https://telegra.ph/INSTRUKCIYA-DLYA-MENEDZhERA--PERVICHNAYA-OBRABOTKA-ZAYAVKI-05-24"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot      = Bot(BOT_TOKEN)
storage  = MemoryStorage()
dp       = Dispatcher(storage=storage)

# ─────────────────────── WEEKLY TOP STORAGE ─────────────────────
weekly_top = {"teams": [], "workers": []}

async def assign_team_leader(chat_id: int):
    # подождать случайное время от 10 до 20 минут
    delay = random.randint(10 * 60, 20 * 60)
    await asyncio.sleep(delay)
    # выбрать случайного тимлидера
    leader = random.choice(TEAM_LEADERS)
    # отправить юзеру уведомление
    await bot.send_message(
        chat_id,
        f"🎉 Вы успешно зачислены в команду! Ваш тимлид - @{leader}!"
    )


def random_top_teams(n):
    """Generate a list of n random teams."""
    teams = []
    for _ in range(n):
        name = random.choice([
            "Fenix", "Professor", "Djenga", "Девятый", "Akatsuki", "Medici", "wa3rix"
        ])
        amount  = random.randint(1000, 10000)
        profits = random.randint(1, 20)
        teams.append({"name": name, "amount": amount, "profits": profits})
    teams.sort(key=lambda x: x['amount'], reverse=True)
    return teams


def random_top_workers(n):
    """Generate a list of n random workers."""
    workers = []
    for _ in range(n):
        name = random.choice([
            "Наташка", "angerfist", "Хорек", "Шарк", "CARAVEL", "Холодрыга", "Не торт"
        ])
        amount  = random.randint(500, 5000)
        profits = random.randint(1, 10)
        workers.append({"name": name, "amount": amount, "profits": profits})
    workers.sort(key=lambda x: x['amount'], reverse=True)
    return workers


def update_weekly_lists():
    """Обновляем списки в weekly_top — вызывается при старте и каждую неделю."""
    weekly_top["teams"]   = random_top_teams(7)
    weekly_top["workers"] = random_top_workers(10)
    logger.info(
        "Weekly lists updated: %d teams, %d workers", 
        len(weekly_top["teams"]), len(weekly_top["workers"]) 
    )


async def weekly_updater():
    """Цикл: каждые понедельник в 10:00 обновляем топ-листы."""
    while True:
        now = dt.datetime.now()
        days_ahead = (0 - now.weekday() + 7) % 7
        if days_ahead == 0 and now.time() >= dt.time(10, 0):
            days_ahead = 7
        next_run = dt.datetime.combine(
            now.date() + dt.timedelta(days=days_ahead),
            dt.time(10, 0)
        )
        delay = (next_run - now).total_seconds()
        logger.info("Next weekly update in %.0f seconds", delay)
        await asyncio.sleep(delay)
        update_weekly_lists()

# ─────────────────────────── USER STORAGE ────────────────────────
user_data = {}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'wallets': [],
            'last_generation': None,
            'total_profit': 0,
            'weekly_profit': 0,
            'referrals': 0,
            'application_done': False
        }
    return user_data[user_id]

# ───────────────────────────── RANKS ─────────────────────────────
RANKS = {
    "Фрешмен": 0,
    "Грайндер": 2000,
    "Ветеран": 5000,
    "Элита": 10000,
    "Легенда": 20000
}

def get_next_rank(total):
    current = max((r for r in RANKS if total >= RANKS[r]), key=lambda r: RANKS[r])
    keys = list(RANKS)
    idx  = keys.index(current)
    if idx < len(keys) - 1:
        nxt = keys[idx + 1]
        need = RANKS[nxt] - total
    else:
        nxt, need = "Максимальный", 0
    return current, nxt, need

# ───────────────────────── FSM APPLICATION ─────────────────────────
class Application(StatesGroup):
    waiting_for_name       = State()
    waiting_for_experience = State()
    waiting_for_hours      = State()
    waiting_for_wallet     = State()


def require_application(handler):
    async def wrapper(message: types.Message, *args, **kwargs):
        if not get_user_data(message.from_user.id)['application_done']:
            await message.answer(
                "⚠️ Сначала заполните анкету: нажмите /start и выберите «Подать заявку»."
            )
            return
        return await handler(message, *args, **kwargs)
    return wrapper

# ───────────────────────── MAIN MENU ─────────────────────────────
def get_main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="Мануалы"))
    kb.row(types.KeyboardButton(text="🧬 Мои кошельки"))
    kb.row(
        types.KeyboardButton(text="📈 Моя статистика"),
        types.KeyboardButton(text="🔝 Топ недели")
    )
    kb.row(
        types.KeyboardButton(text="🔝 Команды"),
        types.KeyboardButton(text="💌 Канал")
    )
    kb.row(
        types.KeyboardButton(text="🤝 Инвайт"),
        types.KeyboardButton(text="🏦 Выплаты")
    )
    return kb.as_markup(resize_keyboard=True)

# ───────────────────────────── HANDLERS ─────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    btn = InlineKeyboardBuilder().add(
        types.InlineKeyboardButton(
            text="✅ Подать заявку", callback_data="apply_from_start"
        )
    )
    welcome_text = (
        "🖼 <b>ДОБРО ПОЖАЛОВАТЬ!</b>\n\n"
        "Ты находишься в нужном месте и в нужное время. Ознакомься с правилами проекта прежде, чем подать заявку.\n\n"
        "⛔ Размещение 18+ медиа любого формата – БАН\n"
        "⛔ Реклама других проектов/услуг без согласования с администрацией – БАН\n"
        "⛔ Попрошайничество – мут на сутки\n"
        "⛔ Срачи на политические темы – БАН моментально\n"
        "⛔ Саботировать/подставлять/провоцировать других участников – БАН\n"
        "⛔ Прием платежей на свои кошельки – БАН\n\n"
        "Подтверждая заявку, ты соглашаешься с правилами ✍️"
    )
    await message.answer(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=btn.as_markup()
    )

@dp.callback_query(lambda c: c.data == "apply_from_start")
async def apply_from_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Application.waiting_for_name)
    await callback.message.answer("1. Укажи свое имя и возраст:")
    await callback.answer()

@dp.message(Application.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name_age=message.text)
    await state.set_state(Application.waiting_for_experience)
    await message.answer("2. Был ли опыт работы на звонках/чатах? (Если был, подробно опишите)")

@dp.message(Application.waiting_for_experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await state.set_state(Application.waiting_for_hours)
    await message.answer("3. Сколько времени готовы уделять работе?")

@dp.message(Application.waiting_for_hours)
async def process_hours(message: types.Message, state: FSMContext):
    await state.update_data(hours=message.text)
    await state.set_state(Application.waiting_for_wallet)
    await message.answer("4. Адрес кошелька с BTC для работы:")

@dp.message(Application.waiting_for_wallet)
async def process_wallet(message: types.Message, state: FSMContext):
    await state.update_data(btc_wallet=message.text)
    data = await state.get_data()
    application_text = (
        "📄 <b>Новая анкета</b>\n\n"
        f"👤 <b>Имя и возраст:</b> {data['name_age']}\n"
        f"💼 <b>Опыт работы:</b> {data['experience']}\n"
        f"⏱ <b>Часы работы:</b> {data['hours']}\n"
        f"💰 <b>BTC кошелёк:</b> {data['btc_wallet']}\n"
        f"🆔 <b>ID пользователя:</b> {message.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_ID, application_text, parse_mode=ParseMode.HTML)
        logger.info("Application sent to admin from user %s", message.from_user.id)
    except Exception as e:
        logger.error("Error sending application: %s", e)

    # Confirmation for user
    await message.answer(
        "✅ <b>Твоя анкета отправлена на рассмотрение.</b>\n",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_kb()
    )
    
    # Channel links
    links = InlineKeyboardBuilder()
    links.row(
        types.InlineKeyboardButton(text="📢 Основной канал", url=MAIN_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💸 Канал выплат", url=PAYMENTS_CHANNEL_LINK)
    )
    await message.answer(
        "Чтобы не пропустить новости и выплаты, подпишись на наши каналы:",
        reply_markup=links.as_markup()
    )
    await state.clear()

    # запланировать уведомление о назначении
    asyncio.create_task(assign_team_leader(message.chat.id))

# Menu option handlers
@dp.message(lambda message: message.text == "Мануалы")
async def show_manuals(message: types.Message):
    manuals_text = (
        "📚 <b>Основные мануалы проекта</b>\n\n"
        "Выберите нужный мануал из списка ниже:"
    )

    # Create inline keyboard with manual links
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="Чем занимаемся",
            url=WHAT_WE_DO_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Настройка Electrum",
            url=ELECTRUM_SETUP_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Отмена BTC транзакций",
            url=CANCEL_TX_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Инструкция для менеджера",
            url=MANAGER_GUIDE_LINK
        )
    )

    await message.answer(
        manuals_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )

@dp.message(lambda message: message.text == "Статистика TL")
async def show_tl_stats(message: types.Message):
    stats_text = (
        "📈 <b>Статистика TL</b>\n"
        "Вы не являетесь тимлидером ни одной команды.\n\n"
        "Чтобы стать тимлидером, проявите активность и обратитесь к @Chill_manoff"
    )
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(lambda message: message.text == "Чем занимаемся")
async def show_what_we_do(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📖 Подробнее о направлении",
        url=WHAT_WE_DO_LINK
    ))
    work_text = (
        "🔹 <b>Основные направления деятельности</b>\n\n"
        "• Настройка Electrum для безопасных транзакций\n"
        "• Отмена BTC транзакций с использованием RBF\n"
        "• Обучение менеджеров для работы с клиентами\n\n"
        "Для получения подробной информации нажмите кнопку ниже:"
    )
    await message.answer(
        work_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )

@dp.message(lambda m: m.text == "🧬 Мои кошельки")
@require_application
async def show_my_wallets(message: types.Message):
    user = get_user_data(message.from_user.id)
    if not user["wallets"]:
        kb = InlineKeyboardBuilder().add(
            types.InlineKeyboardButton(text="🔐 Сгенерировать ключи", callback_data="generate_wallets")
        )
        await message.answer("⚠️ У вас пока нет сгенерированных кошельков.", reply_markup=kb.as_markup())
        return

    text = "🔑 <b>Ваши кошельки для пополнений</b>\n\n"
    for i, w in enumerate(user["wallets"], start=1):
        text += (
            f"<b>Связка #{i}</b> (создана {w['created']})\n"
            f"• ETH: <code>{w['eth']}</code>\n"
            f"• TRX: <code>{w['trx']}</code>\n\n"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data == "generate_wallets")
@require_application
async def generate_keys_callback(callback: types.CallbackQuery):
    user = get_user_data(callback.from_user.id)
    now = time.time()
    if user["last_generation"] and now - user["last_generation"] < 24*3600:
        rem = 24*3600 - (now - user["last_generation"])
        h, m = divmod(rem, 3600)
        m //= 60
        await callback.message.answer(f"⚠️ Вы уже генерировали ключи сегодня.\nСледующая генерация будет доступна через {int(h)}ч {int(m)}м.")
        await callback.answer()
        return

    user["wallets"]        = generate_wallets()
    user["last_generation"] = now

    text = "🎉 <b>Новые кошельки сгенерированы!</b>\n\n"
    for i, w in enumerate(user["wallets"], start=1):
        text += (
            f"<b>Связка #{i}</b>\n"
            f"• ERC20: <code>{w['eth']}</code>\n"
            f"• TRC20: <code>{w['trx']}</code>\n\n"
        )
    text += "‼️ <b>ВАЖНО:</b>\nИспользуйте только эти адреса для получения платежей в нашей команде."
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.message(lambda message: message.text == "📈 Моя статистика")
async def show_my_stats(message: types.Message):
    user = get_user_data(message.from_user.id)
    current_rank, next_rank, needed = get_next_rank(user['total_profit'])

    stats_text = (
        "📊 <b>Ваша статистика</b>\n\n"
        f"💵 Профит за все время: <b>{user['total_profit']}$</b>\n"
        f"📅 Профит за неделю: <b>{user['weekly_profit']}$</b>\n"
        f"🏅 Текущий ранг: <b>{current_rank}</b>\n\n"
        f"📈 До звания <b>{next_rank}</b> осталось: <b>{needed}$</b>\n"
        f"💸 Недельная выплата: <b>{user['weekly_profit'] * 0.35}$</b>"
    )

    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(lambda message: message.text == "🔝 Команды")
async def list_teams(message: types.Message):
    teams = [
        {"name": "Fenix", "amount": 5383, "profits": 11},
        {"name": "Professor", "amount": 5287, "profits": 8},
        {"name": "Djenga", "amount": 4460, "profits": 9},
        {"name": "Девятый", "amount": 3940, "profits": 9},
        {"name": "Akatsuki", "amount": 3389, "profits": 7},
        {"name": "Medici", "amount": 3347, "profits": 8},
        {"name": "wa3rix", "amount": 2606, "profits": 6}
    ]
    
    text = "🏆 <b>Топ команд за неделю</b>\n\n"
    for i, team in enumerate(teams, start=1):
        text += f"{i}. <b>{team['name']}</b> - {team['amount']}$ | профитов: {team['profits']}\n"
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda message: message.text == "🔝 Топ недели")
async def top_week(message: types.Message):
    workers = [
        {"name": "Наташка", "amount": 1700, "profits": 3},
        {"name": "angerfist", "amount": 1601, "profits": 2},
        {"name": "Хорек", "amount": 1494, "profits": 3},
        {"name": "Шарк", "amount": 1493, "profits": 2},
        {"name": "CARAVEL", "amount": 1285, "profits": 2}
    ]
    
    text = "🏆 <b>Топ воркеров недели</b>\n\n"
    for i, w in enumerate(workers, start=1):
        text += f"{i}. <b>{w['name']}</b> - {w['amount']}$ | профитов: {w['profits']}\n"
    text += "\n💸 <b>Канал выплат:</b> " + PAYMENTS_CHANNEL_LINK
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda message: message.text == "💌 Канал")
async def show_channel_info(message: types.Message):
    # Create inline buttons for channels
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="📢 Основной канал",
            url=MAIN_CHANNEL_LINK
        ),
        types.InlineKeyboardButton(
            text="💸 Канал выплат",
            url=PAYMENTS_CHANNEL_LINK
        )
    )

    channel_text = (
        "📢 <b>Наши официальные каналы</b>\n\n"
        "Подпишитесь, чтобы быть в курсе всех обновлений и новостей проекта.\n\n"
        "На случай удаления основного канала, резервным будет канал выплат."
    )

    await message.answer(
        channel_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )

@dp.message(lambda message: message.text == "🤝 Инвайт")
async def generate_invite(message: types.Message):
    bot_username = (await bot.get_me()).username
    ref_code = message.from_user.username or str(message.from_user.id)
    invite_link = f"https://t.me/{bot_username}?start={ref_code}"

    invite_text = (
        "🤝 <b>Пригласите друзей и получайте бонусы!</b>\n\n"
        f"Ваша реферальная ссылка:\n<code>{invite_link}</code>\n\n"
        "За каждого активного реферала вы получаете +5% к недельной выплате!"
    )

    # Create inline button for quick sharing
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📤 Поделиться ссылкой",
        url=f"tg://msg_url?url={invite_link}&text=Присоединяйся%20к%20нашей%20команде!"
    ))

    await message.answer(
        invite_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )

@dp.message(lambda message: message.text == "🏦 Выплаты")
async def show_payments_info(message: types.Message):
    # Create inline button for payments channel
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="💸 Перейти в канал выплат",
        url=PAYMENTS_CHANNEL_LINK
    ))

    payments_text = (
        "💰 <b>Информация о выплатах</b>\n\n"
        "Все профиты публикуются в нашем канале выплат.\n\n"
        "<b>Статистика за неделю:</b>\n"
        "• Топ воркеров: /topweek\n"
        "• Топ команд: /topweekteam\n\n"
        "Выплаты происходят каждый вечер от тимлида."
    )

    await message.answer(
        payments_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )

# Main function
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio

    # Generate initial top lists
    weekly_top["teams"] = [
        {"name": "Fenix", "amount": 5383, "profits": 11},
        {"name": "Professor", "amount": 5287, "profits": 8},
        {"name": "Djenga", "amount": 4460, "profits": 9},
        {"name": "Девятый", "amount": 3940, "profits": 9},
        {"name": "Akatsuki", "amount": 3389, "profits": 7},
        {"name": "Medici", "amount": 3347, "profits": 8},
        {"name": "wa3rix", "amount": 2606, "profits": 6}
    ]
    
    weekly_top["workers"] = [
        {"name": "Наташка", "amount": 1700, "profits": 3},
        {"name": "angerfist", "amount": 1601, "profits": 2},
        {"name": "Хорек", "amount": 1494, "profits": 3},
        {"name": "Шарк", "amount": 1493, "profits": 2},
        {"name": "CARAVEL", "amount": 1285, "profits": 2},
        {"name": "Холодрыга", "amount": 1230, "profits": 2},
        {"name": "Не торт", "amount": 1166, "profits": 3},
        {"name": "ANTAURI", "amount": 1144, "profits": 2},
        {"name": "Цветочек", "amount": 1104, "profits": 3},
        {"name": "ОМНИ", "amount": 1069, "profits": 2}
    ]
    
    asyncio.run(main())
